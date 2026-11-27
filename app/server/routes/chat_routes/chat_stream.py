import asyncio
import logging
from datetime import datetime, timezone
from starlette.datastructures import State
from typing import AsyncIterator, Callable

from typing import Optional
from app.server.routes import sse_frame
from app.server.routes import relay_trace
from app.server.routes import trace_queue
from app.server.routes import drain_trace
from app.server.routes import stored_trace
from app.intelligence.agents import AgentBase
from app.intelligence.tracing import TraceEvent
from app.server.routes import KEEPALIVE_SECONDS
from app.server.chat_sessions import ChatSession
from app.intelligence.messages import MessageBase
from app.intelligence.messages import MessageHuman
from app.intelligence.tracing import TraceEventType
from app.intelligence.tracing import TracingService
from app.intelligence.tracing import TracingServiceBase

logger = logging.getLogger("vela47")


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
    keepalive_seconds: float = KEEPALIVE_SECONDS,
    tracing_service: Optional[TracingServiceBase] = None) -> AsyncIterator[str]:
    yield sse_frame("session", {"id": chat_session.id, "title": chat_session.title, "new": is_new})
    tracing_service = tracing_service if tracing_service is not None else TracingService()
    queue = trace_queue(tracing_service)
    tracing_service.subscribe(lambda event: _log_finding(chat_session, event))

    agent = build_agent(tracing_service)
    agent.restore(chat_session.messages)
    human_message = MessageHuman(content = message)
    work = asyncio.create_task(asyncio.to_thread(agent.execute, human_message))

    async for current_frame in relay_trace(queue, work, keepalive_seconds):
        yield current_frame

    try:
        answer = await work
        response = answer.model_copy(update = {
            "name": agent_name,
            "response_metadata": {
                **answer.response_metadata,
                "trace": stored_trace(tracing_service.events())
            }
        })
        with tracing_service.step("Store", "db", {"conversation": chat_session.id, "new": is_new}) as span:
            await asyncio.to_thread(_remember, state, chat_session, is_new, [human_message, response])
            span["detail"] = ("a new conversation created" if is_new else "2 messages appended") + f", {len(response.response_metadata['trace'])} trace events kept with the answer"
        async for current_frame in drain_trace(queue):
            yield current_frame
        content = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )
        yield sse_frame("answer", {
            "content": content,
            "agent": agent_name,
            "sources": response.response_metadata.get("sources", [])
        })
    except Exception as e:
        logger.exception("Run failed in conversation %s of %s", chat_session.id, chat_session.owner_id)
        tracing_service.emit(TraceEventType.RUN_FAILED, type(e).__name__, {
            "status": "error",
            "error": f"{type(e).__name__}: {e}",
            "detail": str(e)
        })
        async for current_frame in drain_trace(queue):
            yield current_frame
        yield sse_frame("error", {"message": f"{type(e).__name__}: {e}"})
