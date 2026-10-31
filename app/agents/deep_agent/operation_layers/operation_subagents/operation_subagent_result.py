from typing import Literal
from pydantic import BaseModel, Field

from app.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_type import OperationSubagentType


class OperationSubagentResult(BaseModel):
    """What one subagent produced for one task. Deliberately uniform across all
    subagent types: whatever shape a subagent works in internally, it reports
    back as text plus a status, so the merging layer can fold heterogeneous
    results together without knowing which kind of agent produced them. A failed
    subagent yields status='error' rather than raising, so one broken task never
    collapses the whole pipeline."""

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
    status: Literal["success", "error"] = Field(
        default = "success",
        description = "Outcome of the run. 'error' means content holds a failure description "
            "instead of an answer; the merging layer decides whether to report the gap, retry, "
            "or proceed with the remaining results."
    )
