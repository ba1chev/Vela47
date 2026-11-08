from typing import Optional

from app.intelligence.messages import MessageAI
from app.intelligence.agents import OperationType
from app.intelligence.messages import MessageHuman
from app.intelligence.model import ModelFoundation
from app.intelligence.messages import MessageSystem
from app.intelligence.tracing import TraceEventType
from app.intelligence.agents import OperationContext
from app.intelligence.agents import OperationLayerBase
from app.intelligence.tracing import TracingServiceNull
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.agents import MERGING_SYSTEM_PROMPT


class OperationMergingLayer(OperationLayerBase):
    """Folds every subagent result into the single answer the DeepAgent returns.

    This is the layer that justifies threading one OperationContext through the
    pipeline instead of chaining each layer's return value: merging needs the
    original goal and the plan, not just the results. Without them it would be
    synthesising fragments with no way to tell whether they actually answer what
    was asked.

    Each report is written under the step that produced it — the step's instruction,
    then the report with its status. Listed apart, a small model had to pair the
    third result with the third step itself, and a report read without the question
    it answers is easily attributed to the wrong part of the request.

    Errors are passed to the model verbatim rather than filtered out, because a
    gap the user should know about is part of an honest answer.

    The conversation's earlier turns precede the report, so the answer is written
    as the next turn of that conversation rather than as if it had just begun."""

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

    def _instruction(self, context: OperationContext, position: int, task_id: str) -> str:
        task = next((current for current in context.tasks if current.id == task_id), None)
        if task is not None:
            return task.instruction
        if context.plan is not None and position < len(context.plan.steps):
            return context.plan.steps[position].description
        return ""

    def _build_report(self, context: OperationContext) -> str:
        lines: list[str] = [f"REQUEST: {context.goal.content}"]
        for position, current_result in enumerate(context.results):
            lines.extend([
                "",
                f"STEP {position + 1} [{current_result.subagent_type.name}]: {self._instruction(context, position, current_result.task_id)}",
                f"REPORT ({current_result.status}): {current_result.content}"
            ])
        return "\n".join(lines)

    def execute(self, context: OperationContext) -> None:
        parts: list[str] = []
        for current_chunk in self._model.stream([
            MessageSystem(content = MERGING_SYSTEM_PROMPT),
            *context.history,
            MessageHuman(content = self._build_report(context))
        ]):
            parts.append(current_chunk)
            self._tracing_service.emit(
                TraceEventType.ANSWER_CHUNK, "answer", {"text": current_chunk}
            )

        context.final = MessageAI(content = "".join(parts))
