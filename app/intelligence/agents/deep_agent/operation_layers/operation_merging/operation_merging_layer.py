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
    """Folds every subagent result into the single answer the DeepAgent returns. It
    reads the goal and the plan from the shared context, not just the results, so it can
    tell whether they answer what was asked.

    Each report is written under the step that produced it, in plain sentences, followed
    by the facts the system checked on that step on lines marked as such. Listed apart,
    a small model paired reports with the wrong steps; under capitalised labels, it
    copied the labels into the answer. Errors are passed on verbatim, since a gap
    belongs in an honest answer, and the earlier turns come first so the answer
    continues the conversation."""

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
        lines: list[str] = [
            f"The user's request: {context.goal.content}",
            "",
            "The workers' reports, each under the step it answers:" if context.results else "No step was needed for this request."
        ]
        for position, current_result in enumerate(context.results):
            lines.extend([
                "",
                f"Step {position + 1} ({current_result.subagent_type.name}): {self._instruction(context, position, current_result.task_id)}",
                f"Report ({current_result.status}): {current_result.content}",
                *(f"Checked by the system: {current_fact}" for current_fact in current_result.evidence)
            ])
        lines.extend(["", "Write your answer to the user's request now."])
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
