from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional

from app.intelligence.tracing.trace_event import TraceEvent
from app.intelligence.tracing.trace_event_type import TraceEventType


class TracingServiceBase(ABC):
    """Collects what a single run reports about itself. One instance per run, passed
    explicitly to every component that has something to report — never a module-level
    singleton, because the pipeline is built to execute subagents concurrently and a
    shared buffer would interleave unrelated runs into one unreadable stream.

    Components depend on this interface rather than a concrete service, which is what
    lets NullTracingService stand in wherever tracing is not wanted. That is the reason
    nothing in the framework ever checks whether a tracer is present before reporting."""

    @abstractmethod
    def emit(self, type: TraceEventType, label: str,
        payload: Optional[dict[str, Any]] = None,
        duration_ms: Optional[float] = None) -> None:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def events(self) -> list[TraceEvent]:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def subscribe(self, callback: Callable[[TraceEvent], None]) -> None:
        """Registers a listener invoked for every subsequent event. This is what makes
        live streaming possible — the server subscribes and forwards each event to the
        browser as it happens, instead of waiting for the run to finish."""
        raise NotImplementedError("Must be implemented")

    @contextmanager
    def span(self, started: TraceEventType, finished: TraceEventType, label: str,
        payload: Optional[dict[str, Any]] = None) -> Iterator[dict[str, Any]]:
        """Emits a started/finished pair around a block and times it. Yields a dict the
        body may fill in; its contents are merged into the finished event's payload, so
        a caller can report facts it only learns while doing the work. The finished
        event is emitted even when the block raises, so a failed step still closes in
        the UI rather than hanging as in-progress forever."""
        import time

        self.emit(started, label, dict(payload or {}))
        extra: dict[str, Any] = {}
        start = time.perf_counter()
        try:
            yield extra
        finally:
            self.emit(
                finished,
                label,
                {**(payload or {}), **extra},
                (time.perf_counter() - start) * 1000.0
            )
