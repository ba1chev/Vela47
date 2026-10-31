from typing import Optional

from app.intelligence.messages.message_ai import MessageAI
from app.intelligence.messages.message_human import MessageHuman
from app.intelligence.messages.message_system import MessageSystem
from app.intelligence.tracing.trace_event_type import TraceEventType
from app.intelligence.tracing.tracing_service_null import TracingServiceNull
from app.intelligence.tracing.tracing_service_base import TracingServiceBase
from app.intelligence.agents.deep_agent.operation_context import OperationContext
from app.intelligence.model.model_foundation.model_foundation import ModelFoundation
from app.intelligence.agents.deep_agent.prompts.merging_system_prompt import MERGING_SYSTEM_PROMPT
from app.intelligence.agents.deep_agent.operation_layers.operation_layer_type import OperationType
from app.intelligence.agents.deep_agent.operation_layers.operation_layer_base import OperationLayerBase


class OperationMergingLayer(OperationLayerBase):
    """Folds every subagent result into the single answer the DeepAgent returns.

    This is the layer that justifies threading one OperationContext through the
    pipeline instead of chaining each layer's return value: merging needs the
    original goal and the plan, not just the results. Without them it would be
    synthesising fragments with no way to tell whether they actually answer what
    was asked.

    Errors are passed to the model verbatim rather than filtered out, because a
    gap the user should know about is part of an honest answer."""

    def __init__(self, model: ModelFoundation,
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        self._model: ModelFoundation = model
        self._tracing_service: TracingServiceBase = (
            tracing_service
            if tracing_service is not None
            else TracingServiceNull()
        )

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
        parts: list[str] = []
        for current_chunk in self._model.stream([
            MessageSystem(content = MERGING_SYSTEM_PROMPT),
            MessageHuman(content = self._build_report(context))
        ]):
            parts.append(current_chunk)
            self._tracing_service.emit(
                TraceEventType.ANSWER_CHUNK, "answer", {"text": current_chunk}
            )

        context.final = MessageAI(content = "".join(parts))
