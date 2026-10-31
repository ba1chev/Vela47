from typing import Any, Callable, Optional

from app.intelligence.tracing.trace_event import TraceEvent
from app.intelligence.tracing.trace_event_type import TraceEventType
from app.intelligence.tracing.tracing_service_base import TracingServiceBase


class TracingServiceNull(TracingServiceBase):
    """Tracer that discards everything. Exists so components can always hold a
    TracingServiceBase and report unconditionally, instead of guarding every call site
    with a None check. Tracing then costs one no-op method call when it is switched
    off, and the code that reports reads the same whether anyone is listening.

    Deliberately carries no state and no __len__: a component selects between a real
    tracer and this one with an explicit `is not None` check, because any truthiness
    test would silently discard an empty real tracer."""

    def emit(self, type: TraceEventType, label: str,
        payload: Optional[dict[str, Any]] = None,
        duration_ms: Optional[float] = None) -> None:
        return None

    def events(self) -> list[TraceEvent]:
        return []

    def subscribe(self, callback: Callable[[TraceEvent], None]) -> None:
        return None
