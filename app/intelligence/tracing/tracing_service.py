from threading import Lock
from typing import Any, Callable, Optional

from app.intelligence.tracing.trace_event import TraceEvent
from app.intelligence.tracing.trace_event_type import TraceEventType
from app.intelligence.tracing.tracing_service_base import TracingServiceBase


class TracingService(TracingServiceBase):
    """In-memory tracer that both accumulates a run's history and fans each event out
    to live subscribers as it arrives. Those are two different needs — the UI wants
    events the moment they happen, while a caller inspecting a finished run wants the
    whole ordered list — and serving both from one buffer keeps them consistent.

    Guarded by a lock because the subagents layer leases a pool of sandbox slots and is
    built to run those agents concurrently; appends from several threads would otherwise
    corrupt the list. Subscriber callbacks are invoked outside the lock, so a slow
    consumer cannot stall the run that is producing the events."""

    def __init__(self) -> None:
        self._events: list[TraceEvent] = []
        self._subscribers: list[Callable[[TraceEvent], None]] = []
        self._lock: Lock = Lock()

    def emit(self, type: TraceEventType, label: str,
        payload: Optional[dict[str, Any]] = None,
        duration_ms: Optional[float] = None) -> None:
        event = TraceEvent(
            type = type,
            label = label,
            payload = payload or {},
            duration_ms = duration_ms
        )
        with self._lock:
            self._events.append(event)
            subscribers = list(self._subscribers)

        for current_subscriber in subscribers:
            current_subscriber(event)

    def events(self) -> list[TraceEvent]:
        with self._lock:
            return list(self._events)

    def subscribe(self, callback: Callable[[TraceEvent], None]) -> None:
        with self._lock:
            self._subscribers.append(callback)
