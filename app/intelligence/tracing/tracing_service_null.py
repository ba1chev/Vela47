from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional

from app.intelligence.tracing import TraceEvent
from app.intelligence.tracing import TraceEventType
from app.intelligence.tracing import TracingServiceBase


class TracingServiceNull(TracingServiceBase):
    """Tracer that discards everything. Exists so components can always hold a
    TracingServiceBase and report unconditionally, instead of guarding every call site
    with a None check. Tracing then costs one no-op method call when it is switched
    off, and the code that reports reads the same whether anyone is listening.

    Deliberately carries no state and no __len__: a component selects between a real
    tracer and this one with an explicit `is not None` check, because any truthiness
    test would silently discard an empty real tracer.

    Its span() opens nothing, so a component that traces into the void never hides the
    span of a real tracer that is open around it."""

    def emit(self, type: TraceEventType, label: str,
        payload: Optional[dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        span_id: Optional[str] = None,
        parent_id: Optional[str] = None) -> None:
        return None

    def events(self) -> list[TraceEvent]:
        return []

    def subscribe(self, callback: Callable[[TraceEvent], None]) -> None:
        return None

    @contextmanager
    def span(self, started: TraceEventType, finished: TraceEventType, label: str,
        payload: Optional[dict[str, Any]] = None) -> Iterator[dict[str, Any]]:
        yield {}
