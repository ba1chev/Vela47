import json
import asyncio
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


def _frame(event: str, data: dict[str, Any]) -> str:
    """Formats one Server-Sent Events frame. The blank line terminates the frame —
    without it the browser buffers indefinitely waiting for more of the message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _frame_for(event: TraceEvent) -> str:
    """Answer chunks travel the same internal channel as observations but are content,
    not progress, so they leave as their own SSE event — the browser appends them to
    the reply rather than listing them in the trace."""
    if event.type is TraceEventType.ANSWER_CHUNK:
        return _frame("chunk", {"text": event.payload.get("text", "")})
    return _frame("trace", event.model_dump(mode = "json"))


def _remember(state: State, chat_session: ChatSession, is_new: bool, turn: list[MessageBase]) -> None:
    """Makes one finished exchange durable. A new conversation is written only now,
    together with its first exchange, so a run that fails leaves no empty conversation
    behind; an existing one has the exchange appended."""
    store = state.chat_session_store
    if is_new:
        store.create_session(chat_session.model_copy(
            update = {"messages": turn, "updated_at": datetime.now(timezone.utc)}
        ))
    else:
        store.append_messages(chat_session.id, turn)


async def stream_chat(state: State, message: str, chat_session: ChatSession, is_new: bool,
    build_agent: Callable[[TracingServiceBase], AgentBase], agent_name: str) -> AsyncIterator[str]:
    """Streams one exchange. The first frame names the conversation, so the browser
    knows which one a new chat became before any of the answer arrives; the agent is
    built fresh and refilled from the stored conversation, and the exchange is stored
    only once the answer is complete.

    It is handed the app state rather than finding it itself: the conversation store
    belongs to the app, and this runs after the request handler has already returned
    its response.

    Which agent answers is decided by the route and arrives as build_agent, a factory
    that takes this run's tracer — the agent has to be built inside the run, since the
    tracer it reports to is created here. Whatever it answers is marked with agent_name
    before it is stored, so a conversation that moved between agents still shows who
    wrote each reply, and the answer frame carries the sources a RAG answer cites."""
    yield _frame("session", {"id": chat_session.id, "title": chat_session.title, "new": is_new})

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[TraceEvent] = asyncio.Queue()
    tracing_service = TracingService()
    tracing_service.subscribe(
        lambda event: loop.call_soon_threadsafe(queue.put_nowait, event)
    )

    agent = build_agent(tracing_service)
    agent.restore(chat_session.messages)
    human_message = MessageHuman(content = message)
    work = asyncio.create_task(asyncio.to_thread(agent.execute, human_message))

    while True:
        while not queue.empty():
            yield _frame_for(queue.get_nowait())
        if work.done():
            break
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

    while not queue.empty():
        yield _frame_for(queue.get_nowait())

    try:
        response = (await work).model_copy(update = {"name": agent_name})
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
        yield _frame("error", {"message": f"{type(e).__name__}: {e}"})
