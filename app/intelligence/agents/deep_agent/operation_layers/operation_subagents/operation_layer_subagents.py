from typing import Optional

from app.intelligence.messages.message_human import MessageHuman
from app.intelligence.tracing.trace_event_type import TraceEventType
from app.intelligence.tracing.tracing_service_null import TracingServiceNull
from app.intelligence.tracing.tracing_service_base import TracingServiceBase
from app.intelligence.agents.deep_agent.operation_context import OperationContext
from app.intelligence.agents.deep_agent.operation_layers.operation_layer_type import OperationType
from app.intelligence.agents.deep_agent.operation_layers.operation_layer_base import OperationLayerBase
from app.intelligence.agents.deep_agent.operation_layers.operation_decomposition.operation_task import OperationTask
from app.intelligence.agents.deep_agent.operation_layers.operation_sanbox.operation_sandbox_pool_base import OperationSandboxPoolBase
from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_result import OperationSubagentResult
from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_subagents_factory.operation_subagent_factory_base import OperationSubagentFactoryBase


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
    subagent cannot leak a slot and starve the rest of the run."""

    def __init__(self, subagent_factory: OperationSubagentFactoryBase,
        sandbox_pool: OperationSandboxPoolBase,
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        self._subagent_factory: OperationSubagentFactoryBase = subagent_factory
        self._sandbox_pool: OperationSandboxPoolBase = sandbox_pool
        self._tracing_service: TracingServiceBase = (
            tracing_service
            if tracing_service is not None
            else TracingServiceNull()
        )

    @property
    def operation_type(self) -> OperationType:
        return OperationType.SUBAGENTS

    def _run_task(self, task: OperationTask) -> OperationSubagentResult:
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
                    subagent = self._subagent_factory.create(task.subagent_type)
                    response = subagent.execute(MessageHuman(content = task.instruction))
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
        context.results = [self._run_task(current_task) for current_task in context.tasks]
