from pydantic import BaseModel, Field

from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_type import OperationSubagentType


class OperationStep(BaseModel):
    """A single unit of work in an OperationPlan, as produced by the planning
    layer. A step describes intent — what needs to happen and which kind of
    subagent should handle it — but carries no execution detail. The
    decomposition layer turns each step into a concrete OperationTask."""

    index: int = Field(
        ge = 0,
        description = "Zero-based position of this step within the plan. Defines execution "
            "order and is carried through to the resulting OperationTask so results can "
            "be traced back to the step that produced them."
    )
    description: str = Field(
        description = "What this step must accomplish, phrased as an instruction the assigned "
            "subagent can act on directly. Written by the planning model, so it reflects the "
            "model's decomposition of the original goal rather than a fixed template."
    )
    subagent_type: OperationSubagentType = Field(
        description = "Which kind of subagent should carry out this step. Resolved by "
            "OperationSubagentFactory into a concrete agent with its own tool, model and "
            "context window policy."
    )
