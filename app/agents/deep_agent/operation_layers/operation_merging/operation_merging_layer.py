from app.messages.message_human import MessageHuman
from app.messages.message_system import MessageSystem
from app.agents.deep_agent.operation_context import OperationContext
from app.agents.deep_agent.system_prompt import MERGING_SYSTEM_PROMPT
from app.model.model_foundation.model_foundation import ModelFoundation
from app.agents.deep_agent.operation_layers.operation_layer_type import OperationType
from app.agents.deep_agent.operation_layers.operation_layer_base import OperationLayerBase


class OperationMergingLayer(OperationLayerBase):
    """Folds every subagent result into the single answer the DeepAgent returns.

    This is the layer that justifies threading one OperationContext through the
    pipeline instead of chaining each layer's return value: merging needs the
    original goal and the plan, not just the results. Without them it would be
    synthesising fragments with no way to tell whether they actually answer what
    was asked.

    Errors are passed to the model verbatim rather than filtered out, because a
    gap the user should know about is part of an honest answer."""

    def __init__(self, model: ModelFoundation) -> None:
        self._model: ModelFoundation = model

    @property
    def operation_type(self) -> OperationType:
        return OperationType.MERGING

    def _build_report(self, context: OperationContext) -> str:
        lines: list[str] = [f"GOAL: {context.goal.content}", ""]

        if context.plan is not None:
            lines.append("PLAN:")
            lines.extend(
                f"  {current_step.index}. [{current_step.subagent_type.name}] {current_step.description}"
                for current_step in context.plan.steps
            )
            lines.append("")

        lines.append("SUBAGENT RESULTS:")
        lines.extend(
            f"  [{current_result.subagent_type.name}] ({current_result.status}) {current_result.content}"
            for current_result in context.results
        )
        return "\n".join(lines)

    def execute(self, context: OperationContext) -> None:
        context.final = self._model.invoke([
            MessageSystem(content = MERGING_SYSTEM_PROMPT),
            MessageHuman(content = self._build_report(context))
        ])
