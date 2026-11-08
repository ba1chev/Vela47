from typing import Literal
from pydantic import BaseModel, Field

from app.intelligence.agents import OperationSubagentType


class OperationSubagentResult(BaseModel):
    """What one subagent produced for one task. Deliberately uniform across all
    subagent types: whatever shape a subagent works in internally, it reports
    back as text plus a status, so the merging layer can fold heterogeneous
    results together without knowing which kind of agent produced them. A failed
    subagent yields status='error' rather than raising, so one broken task never
    collapses the whole pipeline.

    Beside the subagent's own account of its work, a result carries the evidence the
    system's probes gathered on the same step — files really written, tests really run,
    pages really read. The two are kept apart because they are not equally reliable:
    the content is what the model says, the evidence is what happened."""

    task_id: str = Field(
        description = "The id of the OperationTask this result answers. Echoed back verbatim so "
            "the merging layer can pair results with tasks."
    )
    subagent_type: OperationSubagentType = Field(
        description = "Which kind of subagent produced this result. Lets the merging layer weigh "
            "or group contributions by origin — e.g. treating REVIEW output as commentary on "
            "CODE output rather than as a peer result."
    )
    content: str = Field(
        description = "The subagent's answer as plain text. For agents that parse their response "
            "into a typed OutputBase, this holds the serialised form — the typed value stays "
            "inside the subagent and never crosses the layer boundary."
    )
    evidence: list[str] = Field(
        default_factory = list,
        description = "Facts the system checked for itself after the step, one sentence each — "
            "'Files created: primes.py (9 lines).', 'The system ran the tests after this step: All "
            "tests passed.' Empty when the subagent's type has no probes or the step failed."
    )
    status: Literal["success", "error"] = Field(
        default = "success",
        description = "Outcome of the run. 'error' means content holds a failure description "
            "instead of an answer; the merging layer decides whether to report the gap, retry, "
            "or proceed with the remaining results."
    )
