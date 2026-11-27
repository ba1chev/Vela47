import json
import asyncio
import logging
from datetime import datetime, timezone
from starlette.datastructures import State
from typing import Any, AsyncIterator, Callable

from app.intelligence.agents import AgentBase
from app.intelligence.tracing import TraceEvent
from app.server.chat_sessions import ChatSession
from app.intelligence.messages import MessageBase
from app.intelligence.messages import MessageHuman
from app.intelligence.tracing import TraceEventType
from app.intelligence.tracing import TracingService
from app.intelligence.tracing import TracingServiceBase

POLL_INTERVAL_SECONDS = 0.05
KEEPALIVE_SECONDS = 15.0
KEEPALIVE_FRAME = ": keep-alive\n\n"
TRACE_TEXT_CHARS = 300
UNSTORED_TRACE_EVENTS = {
    TraceEventType.ANSWER_CHUNK,
    TraceEventType.SANDBOX_ACQUIRED,
    TraceEventType.SANDBOX_RELEASED
}

logger = logging.getLogger("vela47")


def _frame(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _frame_for(event: TraceEvent) -> str:
    if event.type is TraceEventType.ANSWER_CHUNK:
        return _frame("chunk", {"text": event.payload.get("text", "")})
    return _frame("trace", event.model_dump(mode = "json"))


def _shorten(value: Any) -> Any:
    if isinstance(value, str):
        return value if len(value) <= TRACE_TEXT_CHARS else value[:TRACE_TEXT_CHARS - 1].rstrip() + "…"
    if isinstance(value, list):
        return [_shorten(current) for current in value]
    if isinstance(value, dict):
        return {key: _shorten(current) for key, current in value.items()}
    return value


def _stored_trace(events: list[TraceEvent]) -> list[dict[str, Any]]:
    return [
        _shorten(current_event.model_dump(mode = "json"))
        for current_event in events
        if current_event.type not in UNSTORED_TRACE_EVENTS
    ]


def _log_finding(chat_session: ChatSession, event: TraceEvent) -> None:
    if event.type is not TraceEventType.SECURITY_FLAGGED:
        return
    logger.warning(
        "Security finding in conversation %s of %s: %s (%s)",
        chat_session.id,
        chat_session.owner_id,
        event.label,
        ", ".join(event.payload.get("matches", {}))
    )


def _remember(state: State, chat_session: ChatSession, is_new: bool, turn: list[MessageBase]) -> None:
    store = state.chat_session_store
    if is_new:
        store.create_session(chat_session.model_copy(
            update = {"messages": turn, "updated_at": datetime.now(timezone.utc)}
        ))
    else:
        store.append_messages(chat_session.id, turn)


async def stream_chat(state: State, message: str, chat_session: ChatSession, is_new: bool,
    build_agent: Callable[[TracingServiceBase], AgentBase], agent_name: str,
    keepalive_seconds: float = KEEPALIVE_SECONDS) -> AsyncIterator[str]:
    yield _frame("session", {"id": chat_session.id, "title": chat_session.title, "new": is_new})

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[TraceEvent] = asyncio.Queue()
    tracing_service = TracingService()
    tracing_service.subscribe(
        lambda event: loop.call_soon_threadsafe(queue.put_nowait, event)
    )
    tracing_service.subscribe(lambda event: _log_finding(chat_session, event))

    agent = build_agent(tracing_service)
    agent.restore(chat_session.messages)
    human_message = MessageHuman(content = message)
    work = asyncio.create_task(asyncio.to_thread(agent.execute, human_message))

    last_frame_at = loop.time()
    while True:
        while not queue.empty():
            yield _frame_for(queue.get_nowait())
            last_frame_at = loop.time()
        if work.done():
            break
        if loop.time() - last_frame_at >= keepalive_seconds:
            yield KEEPALIVE_FRAME
            last_frame_at = loop.time()
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

    while not queue.empty():
        yield _frame_for(queue.get_nowait())

    try:
        answer = await work
        response = answer.model_copy(update = {
            "name": agent_name,
            "response_metadata": {
                **answer.response_metadata,
                "trace": _stored_trace(tracing_service.events())
            }
        })
        await asyncio.to_thread(_remember, state, chat_session, is_new, [human_message, response])
        content = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )
        yield _frame("answer", {
            "content": content,
            "agent": agent_name,
            "sources": response.response_metadata.get("sources", [])
        })
    except Exception as e:
        logger.exception("Run failed in conversation %s of %s", chat_session.id, chat_session.owner_id)
        yield _frame("error", {"message": f"{type(e).__name__}: {e}"})
