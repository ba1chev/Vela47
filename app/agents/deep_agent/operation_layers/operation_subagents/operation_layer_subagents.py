from app.messages.message_human import MessageHuman
from app.agents.deep_agent.operation_context import OperationContext
from app.agents.deep_agent.operation_layers.operation_layer_type import OperationType
from app.agents.deep_agent.operation_layers.operation_layer_base import OperationLayerBase
from app.agents.deep_agent.operation_layers.operation_decomposition.operation_task import OperationTask
from app.agents.deep_agent.operation_layers.operation_sanbox.operation_sandbox_pool_base import OperationSandboxPoolBase
from app.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_result import OperationSubagentResult
from app.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_factory_base import OperationSubagentFactoryBase


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
        sandbox_pool: OperationSandboxPoolBase) -> None:
        self._subagent_factory: OperationSubagentFactoryBase = subagent_factory
        self._sandbox_pool: OperationSandboxPoolBase = sandbox_pool

    @property
    def operation_type(self) -> OperationType:
        return OperationType.SUBAGENTS

    def _run_task(self, task: OperationTask) -> OperationSubagentResult:
        slot = self._sandbox_pool.acquire()
        try:
            subagent = self._subagent_factory.create(task.subagent_type)
            response = subagent.execute(MessageHuman(content = task.instruction))
            return OperationSubagentResult(
                task_id = task.id,
                subagent_type = task.subagent_type,
                content = response.content
                if isinstance(response.content, str)
                else str(response.content),
                status = "success"
            )
        except Exception as e:
            return OperationSubagentResult(
                task_id = task.id,
                subagent_type = task.subagent_type,
                content = str(e),
                status = "error"
            )
        finally:
            self._sandbox_pool.release(slot)

    def execute(self, context: OperationContext) -> None:
        context.results = [self._run_task(current_task) for current_task in context.tasks]
