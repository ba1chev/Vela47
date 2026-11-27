from uuid import uuid4
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from app.intelligence.tracing import TraceEventType


class TraceEvent(BaseModel):
    """One observation recorded during a run. Carries both a human-readable label
    and a structured payload so the same event can drive a progress line in the UI
    and be inspected programmatically without parsing prose.

    Events are immutable records of something that already happened — the
    timestamp is stamped at construction and never set by the caller, which keeps
    ordering honest even when a producer batches its reporting.

    span_id and parent_id make the events a tree: the started and finished events of
    one span share its id, and everything reported while it is open names it as the
    parent. The tree is therefore exact however events interleave."""

    type: TraceEventType = Field(
        description = "What kind of occurrence this is. The UI dispatches on this value to "
            "decide how to render the event, so adding a type is a contract change the "
            "frontend must also learn about."
    )
    label: str = Field(
        description = "Short human-readable description shown directly in the UI — e.g. "
            "'Planning' or 'RESEARCH subagent'. Written for a reader watching the run, not "
            "for a log parser."
    )
    timestamp: datetime = Field(
        default_factory = lambda: datetime.now(timezone.utc),
        description = "When the event was recorded, in UTC. Stamped automatically at "
            "construction so producers cannot report a misleading ordering."
    )
    payload: dict[str, Any] = Field(
        default_factory = dict,
        description = "Structured detail specific to this event type — the step count for a "
            "finished plan, the token usage for a model call, the slot id for a sandbox "
            "lease. Must be JSON-serialisable, since it is sent to the browser verbatim."
    )
    span_id: str = Field(
        default_factory = lambda: uuid4().hex[:16],
        description = "Id of the span this event belongs to. Shared by the started and finished "
            "events of one span; every other event gets one of its own."
    )
    parent_id: Optional[str] = Field(
        default = None,
        description = "Id of the span that was open when this event was reported, or None at the "
            "top of a run."
    )
    duration_ms: Optional[float] = Field(
        default = None,
        description = "How long the described work took, in milliseconds. Populated only on "
            "finished-style events; None on instantaneous ones."
    )
