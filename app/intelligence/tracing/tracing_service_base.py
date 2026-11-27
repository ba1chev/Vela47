import time
from uuid import uuid4
from contextvars import ContextVar
from abc import ABC, abstractmethod
from contextlib import contextmanager, AbstractContextManager
from typing import Any, Callable, Iterator, Optional

from app.intelligence.tracing import TraceEvent
from app.intelligence.tracing import TraceEventType

CURRENT_SPAN: ContextVar[Optional[tuple[int, str]]] = ContextVar("vela47_current_span", default = None)


class TracingServiceBase(ABC):
    """Collects what a single run reports about itself. One instance per run, passed
    explicitly to every component that has something to report — never a module-level
    singleton, because the pipeline is built to execute subagents concurrently and a
    shared buffer would interleave unrelated runs into one unreadable stream.

    span() opens a span, and every event reported inside it, from any depth of the call
    stack, gets that span as its parent. That is what lets the trace be a tree without a
    component knowing who called it. A span the body leaves by an exception finishes with
    status "error" and the exception, and the exception still propagates.

    Components depend on this interface rather than a concrete service, which is what
    lets TracingServiceNull stand in wherever tracing is not wanted."""

    @abstractmethod
    def emit(self, type: TraceEventType, label: str,
        payload: Optional[dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        span_id: Optional[str] = None,
        parent_id: Optional[str] = None) -> None:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def events(self) -> list[TraceEvent]:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def subscribe(self, callback: Callable[[TraceEvent], None]) -> None:
        raise NotImplementedError("Must be implemented")

    def current_span_id(self) -> Optional[str]:
        current = CURRENT_SPAN.get()
        if current is None or current[0] != id(self):
            return None
        return current[1]

    @contextmanager
    def span(self, started: TraceEventType, finished: TraceEventType, label: str,
        payload: Optional[dict[str, Any]] = None) -> Iterator[dict[str, Any]]:

        span_id = uuid4().hex[:16]
        parent_id = self.current_span_id()
        self.emit(started, label, dict(payload or {}), span_id = span_id, parent_id = parent_id)
        token = CURRENT_SPAN.set((id(self), span_id))
        extra: dict[str, Any] = {}
        start = time.perf_counter()
        try:
            yield extra
        except BaseException as error:
            extra.setdefault("status", "error")
            extra.setdefault("error", f"{type(error).__name__}: {error}")
            raise
        finally:
            CURRENT_SPAN.reset(token)
            self.emit(
                finished,
                label,
                {**(payload or {}), **extra},
                (time.perf_counter() - start) * 1000.0,
                span_id = span_id,
                parent_id = parent_id
            )

    def step(self, label: str, category: str,
        payload: Optional[dict[str, Any]] = None) -> AbstractContextManager[dict[str, Any]]:
        return self.span(
            TraceEventType.STEP_STARTED,
            TraceEventType.STEP_FINISHED,
            label,
            {"category": category, **(payload or {})}
        )

    def record(self, label: str, category: str,
        payload: Optional[dict[str, Any]] = None,
        duration_ms: Optional[float] = None) -> None:
        self.emit(TraceEventType.STEP_RECORDED, label, {"category": category, **(payload or {})}, duration_ms)
