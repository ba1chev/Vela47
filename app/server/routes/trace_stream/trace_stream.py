import json
import asyncio
from typing import Any, AsyncIterator

from app.intelligence.tracing import TraceEvent
from app.intelligence.tracing import TraceEventType
from app.intelligence.tracing import TracingServiceBase

POLL_INTERVAL_SECONDS = 0.05
KEEPALIVE_SECONDS = 15.0
KEEPALIVE_FRAME = ": keep-alive\n\n"
TRACE_TEXT_CHARS = 20_000
UNSTORED_TRACE_EVENTS = {
    TraceEventType.ANSWER_CHUNK,
    TraceEventType.SANDBOX_ACQUIRED,
    TraceEventType.SANDBOX_RELEASED
}


def sse_frame(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def trace_frame(event: TraceEvent) -> str:
    if event.type is TraceEventType.ANSWER_CHUNK:
        return sse_frame("chunk", {"text": event.payload.get("text", "")})
    return sse_frame("trace", event.model_dump(mode = "json"))


def shorten_trace_text(value: Any) -> Any:
    if isinstance(value, str):
        return value if len(value) <= TRACE_TEXT_CHARS else value[:TRACE_TEXT_CHARS - 1].rstrip() + "…"
    if isinstance(value, list):
        return [shorten_trace_text(current) for current in value]
    if isinstance(value, dict):
        return {key: shorten_trace_text(current) for key, current in value.items()}
    return value


def stored_trace(events: list[TraceEvent]) -> list[dict[str, Any]]:
    return [
        shorten_trace_text(current_event.model_dump(mode = "json"))
        for current_event in events
        if current_event.type not in UNSTORED_TRACE_EVENTS
    ]


def trace_queue(tracing_service: TracingServiceBase) -> asyncio.Queue[TraceEvent]:
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[TraceEvent] = asyncio.Queue()
    tracing_service.subscribe(lambda event: loop.call_soon_threadsafe(queue.put_nowait, event))
    return queue


async def relay_trace(queue: asyncio.Queue[TraceEvent], work: asyncio.Future,
    keepalive_seconds: float = KEEPALIVE_SECONDS) -> AsyncIterator[str]:
    loop = asyncio.get_running_loop()
    last_frame_at = loop.time()
    while True:
        while not queue.empty():
            yield trace_frame(queue.get_nowait())
            last_frame_at = loop.time()
        if work.done():
            break
        if loop.time() - last_frame_at >= keepalive_seconds:
            yield KEEPALIVE_FRAME
            last_frame_at = loop.time()
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

    while not queue.empty():
        yield trace_frame(queue.get_nowait())
