from enum import Enum


class TraceEventType(str, Enum):
    """Enumerates everything a run can report about itself. Inherits from str so
    each value serialises to a readable token over the wire — the UI switches on
    these strings directly, with no mapping layer between the framework and the
    browser.

    Events come in started/finished pairs wherever a duration is meaningful, so a
    consumer can render a step as in-progress the moment it begins rather than
    only once it completes. Single events are used where the thing being reported
    is instantaneous.

    The STEP_* types are the general-purpose ones: any stage that has no type of its own
    (reading a file, a database write, an authorization decision) reports as a step
    and names what it is in the payload's "category", so a new kind of step needs no
    new type and no new contract with the browser."""

    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_FINISHED = "pipeline_finished"
    LAYER_STARTED = "layer_started"
    LAYER_FINISHED = "layer_finished"
    SUBAGENT_STARTED = "subagent_started"
    SUBAGENT_FINISHED = "subagent_finished"
    SANDBOX_ACQUIRED = "sandbox_acquired"
    SANDBOX_RELEASED = "sandbox_released"
    MODEL_INVOKED = "model_invoked"
    TOOL_STARTED = "tool_started"
    TOOL_EXECUTED = "tool_executed"
    A2A_STARTED = "a2a_started"
    A2A_FINISHED = "a2a_finished"
    SECURITY_CHECKED = "security_checked"
    SECURITY_FLAGGED = "security_flagged"
    RUN_FAILED = "run_failed"
    ANSWER_CHUNK = "answer_chunk"
    STEP_STARTED = "step_started"
    STEP_FINISHED = "step_finished"
    STEP_RECORDED = "step_recorded"
