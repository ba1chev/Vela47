from pydantic import BaseModel, Field

from app.agents.deep_agent.operation_layers.operation_planning.operation_step import OperationStep


class OperationPlan(BaseModel):
    """The planning layer's structured output — an ordered breakdown of the
    original goal into steps, each assigned to a kind of subagent. Doubles as
    the JSON schema handed to the planning model, so the shape the model is
    asked to produce and the shape the pipeline consumes can never drift apart."""

    goal: str = Field(
        description = "The original user goal restated in the planner's own words. Kept on the "
            "plan so later layers can judge whether the steps still serve the request without "
            "re-reading the raw conversation."
    )
    steps: list[OperationStep] = Field(
        description = "The ordered steps that together satisfy the goal. Each becomes exactly "
            "one OperationTask in the decomposition layer, so the number of steps bounds how "
            "many subagents the pipeline will run."
    )
