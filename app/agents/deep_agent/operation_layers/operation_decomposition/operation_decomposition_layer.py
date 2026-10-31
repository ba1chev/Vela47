from uuid import uuid4

from app.agents.deep_agent.operation_context import OperationContext
from app.agents.deep_agent.operation_layers.operation_layer_type import OperationType
from app.agents.deep_agent.operation_layers.operation_layer_base import OperationLayerBase
from app.agents.deep_agent.operation_layers.operation_decomposition.operation_task import OperationTask


class OperationDecompositionLayer(OperationLayerBase):
    """Materialises the plan's steps into dispatchable tasks, one task per step.
    Deliberately deterministic — no model call. The planning layer already decided
    what the work is; asking a model to restate that decision would add latency
    and a second chance to hallucinate without adding information. This layer's
    job is to assign stable identities so results can be correlated back, and to
    freeze the instruction each subagent will receive verbatim.

    Running with no plan leaves tasks empty rather than raising, so a pipeline
    configured without a planning stage degrades to doing nothing here instead
    of crashing."""

    @property
    def operation_type(self) -> OperationType:
        return OperationType.DECOMPOSITION

    def execute(self, context: OperationContext) -> None:
        if context.plan is None:
            return

        context.tasks = [
            OperationTask(
                id = str(uuid4()),
                step_index = current_step.index,
                subagent_type = current_step.subagent_type,
                instruction = current_step.description
            )
            for current_step in context.plan.steps
        ]
