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
    """Runs one freshly built subagent per task inside a leased sandbox slot and
    collects what each produced.

    Every task is isolated twice over: a new agent with empty memory, and an
    environment leased from the pool for the duration of the run and returned
    afterwards. The pool's fixed size is what bounds concurrency — there is no
    separate limit here, because a pool of ten slots already means at most ten
    subagents.

    A failing subagent is recorded as an error result rather than propagated.
    One subagent that cannot complete its step should not discard the work of
    the others; the merging layer sees the failure and decides how to report
    the gap. Slot release happens in a finally block so a crash inside a
    subagent cannot leak a slot and starve the rest of the run.

    A subagent is handed its instruction together with the user's goal, through
    SUBAGENT_TASK_TEMPLATE, so a step that says 'the hackathon' can be done for the
    hackathon the user meant. The plan and the other tasks stay out of view."""

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
                    content = (
                        response.content
                        if isinstance(response.content, str)
                        else str(response.content)
                    )
                    status = "success"
                except Exception as e:
                    content = str(e)
                    status = "error"
                span["status"] = status
                span["result"] = content
            return OperationSubagentResult(
                task_id = task.id,
                subagent_type = task.subagent_type,
                content = content,
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
