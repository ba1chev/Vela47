from pydantic import BaseModel, Field

from app.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_type import OperationSubagentType


class OperationTask(BaseModel):
    """A dispatchable unit of work produced by the decomposition layer. Where an
    OperationStep expresses intent, a task is the executable form — it carries a
    stable id so its result can be correlated back, and an instruction phrased as
    the message that will be handed to the subagent verbatim."""

    id: str = Field(
        description = "Stable identifier for this task, generated at decomposition time. The "
            "matching OperationSubagentResult echoes it back, which is what lets the merging "
            "layer pair results with the tasks that produced them regardless of ordering."
    )
    step_index: int = Field(
        ge = 0,
        description = "Index of the OperationStep this task was derived from. Preserves the "
            "link to the plan so a result can be traced to the reasoning that requested it."
    )
    subagent_type: OperationSubagentType = Field(
        description = "Which kind of subagent must execute this task, inherited from the "
            "originating step. OperationSubagentFactory uses it to build the agent."
    )
    instruction: str = Field(
        description = "The exact instruction handed to the subagent as a MessageHuman. Self-"
            "contained by construction — a subagent sees only this, never the plan or the "
            "other tasks, which is what keeps subagents single-responsibility."
    )
