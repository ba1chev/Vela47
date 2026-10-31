from typing import Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.intelligence.tracing.trace_event_type import TraceEventType


class TraceEvent(BaseModel):
    """One observation recorded during a run. Carries both a human-readable label
    and a structured payload so the same event can drive a progress line in the UI
    and be inspected programmatically without parsing prose.

    Events are immutable records of something that already happened — the
    timestamp is stamped at construction and never set by the caller, which keeps
    ordering honest even when a producer batches its reporting."""

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
    duration_ms: Optional[float] = Field(
        default = None,
        description = "How long the described work took, in milliseconds. Populated only on "
            "finished-style events; None on instantaneous ones."
    )
