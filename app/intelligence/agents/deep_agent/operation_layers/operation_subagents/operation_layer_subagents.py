from typing import Optional

from app.intelligence.agents import OperationType
from app.intelligence.agents import OperationTask
from app.intelligence.messages import MessageHuman
from app.intelligence.tracing import TraceEventType
from app.intelligence.sandbox import SandboxPoolBase
from app.intelligence.agents import OperationContext
from app.intelligence.agents import OperationLayerBase
from app.intelligence.tracing import TracingServiceNull
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.agents import SUBAGENT_TASK_TEMPLATE
from app.intelligence.agents import OperationSubagentResult
from app.intelligence.agents import OperationSubagentFactoryBase


class OperationSubagentsLayer(OperationLayerBase):
    """Runs one freshly built subagent per task in a leased sandbox slot and collects
    what each produced: the report, and beside it the evidence its probes gathered. The
    pool's fixed size is the only concurrency limit.

    A failing subagent becomes an error result, with no evidence, instead of raising, so
    one broken step does not discard the others, and the slot is released in a finally
    block. Each subagent sees its instruction and the user's goal through
    SUBAGENT_TASK_TEMPLATE, never the plan or the other tasks."""

    def __init__(self, subagent_factory: OperationSubagentFactoryBase,
        sandbox_pool: SandboxPoolBase,
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        self._subagent_factory: OperationSubagentFactoryBase = subagent_factory
        self._sandbox_pool: SandboxPoolBase = sandbox_pool
        self._tracing_service: TracingServiceBase = (
            tracing_service
            if tracing_service is not None
            else TracingServiceNull()
        )

    @property
    def operation_type(self) -> OperationType:
        return OperationType.SUBAGENTS

    def _message(self, task: OperationTask) -> MessageHuman:
        if not task.goal:
            return MessageHuman(content = task.instruction)
        return MessageHuman(content = SUBAGENT_TASK_TEMPLATE.format(instruction = task.instruction, goal = task.goal))

    def _run_task(self, task: OperationTask, run_id: str) -> OperationSubagentResult:
        slot = self._sandbox_pool.acquire()
        self._tracing_service.emit(
            TraceEventType.SANDBOX_ACQUIRED,
            f"slot {slot.id}",
            {"slot": slot.id, "available": self._sandbox_pool.available, "task_id": task.id}
        )
        try:
            with self._tracing_service.span(
                TraceEventType.SUBAGENT_STARTED,
                TraceEventType.SUBAGENT_FINISHED,
                task.subagent_type.name,
                {"task_id": task.id, "slot": slot.id, "instruction": task.instruction}
            ) as span:
                try:
                    sandbox_env = self._sandbox_pool.env_for(slot, run_id)
                    subagent = self._subagent_factory.create(task.subagent_type, sandbox_env)
                    response = subagent.execute(self._message(task))
                    evidence = subagent.evidence
                    content = (
                        response.content
                        if isinstance(response.content, str)
                        else str(response.content)
                    )
                    status = "success"
                except Exception as e:
                    content = str(e)
                    evidence = []
                    status = "error"
                span["status"] = status
                span["result"] = content
                span["evidence"] = evidence
            return OperationSubagentResult(
                task_id = task.id,
                subagent_type = task.subagent_type,
                content = content,
                evidence = evidence,
                status = status
            )
        finally:
            self._sandbox_pool.release(slot)
            self._tracing_service.emit(
                TraceEventType.SANDBOX_RELEASED,
                f"slot {slot.id}",
                {"slot": slot.id, "available": self._sandbox_pool.available}
            )

    def execute(self, context: OperationContext) -> None:
        context.results = [
            self._run_task(current_task, context.run_id) for current_task in context.tasks
        ]
