from enum import Enum


class TraceEventType(str, Enum):
    """Enumerates everything a run can report about itself. Inherits from str so
    each value serialises to a readable token over the wire — the UI switches on
    these strings directly, with no mapping layer between the framework and the
    browser.

    Events come in started/finished pairs wherever a duration is meaningful, so a
    consumer can render a step as in-progress the moment it begins rather than
    only once it completes. Single events are used where the thing being reported
    is instantaneous."""

    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_FINISHED = "pipeline_finished"
    LAYER_STARTED = "layer_started"
    LAYER_FINISHED = "layer_finished"
    SUBAGENT_STARTED = "subagent_started"
    SUBAGENT_FINISHED = "subagent_finished"
    SANDBOX_ACQUIRED = "sandbox_acquired"
    SANDBOX_RELEASED = "sandbox_released"
    MODEL_INVOKED = "model_invoked"
    TOOL_EXECUTED = "tool_executed"
    RUN_FAILED = "run_failed"
