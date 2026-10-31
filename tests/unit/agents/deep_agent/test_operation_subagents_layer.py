import pathlib
import tempfile

from app.intelligence.agents import OperationTask
from app.intelligence.agents import OperationType
from app.intelligence.messages import MessageHuman
from app.intelligence.tracing import TracingService
from app.intelligence.tracing import TraceEventType
from app.intelligence.agents import OperationContext
from app.intelligence.sandbox import SandboxPoolInMemory
from app.intelligence.agents import OperationSubagentType
from app.intelligence.agents import OperationSubagentsLayer
from tests.fixtures.agents.stub_subagent_factory import StubSubagentFactory


def make_context(count = 2):
    return OperationContext(
        goal = MessageHuman(content = "goal"),
        tasks = [OperationTask(id = f"t{i}", step_index = i,
            subagent_type = OperationSubagentType.CODE,
            instruction = f"task {i}") for i in range(count)])


def make_pool(size = 3):
    return SandboxPoolInMemory(size = size, base_directory = pathlib.Path(tempfile.mkdtemp()))


class TestOperationSubagentsLayer:
    def test_its_type_is_subagents(self):
        layer = OperationSubagentsLayer(StubSubagentFactory(), make_pool())
        assert layer.operation_type is OperationType.SUBAGENTS

    def test_one_result_per_task(self):
        context = make_context(3)
        OperationSubagentsLayer(StubSubagentFactory(), make_pool()).execute(context)
        assert len(context.results) == 3

    def test_results_carry_their_task_id(self):
        context = make_context(2)
        OperationSubagentsLayer(StubSubagentFactory(), make_pool()).execute(context)
        assert [r.task_id for r in context.results] == ["t0", "t1"]

    def test_the_subagent_answer_becomes_the_result(self):
        context = make_context(1)
        OperationSubagentsLayer(StubSubagentFactory(), make_pool()).execute(context)
        assert context.results[0].content == "did task 0"

    def test_every_slot_is_returned_to_the_pool(self):
        pool = make_pool(2)
        OperationSubagentsLayer(StubSubagentFactory(), pool).execute(make_context(2))
        assert pool.available == 2

    def test_a_failing_subagent_becomes_an_error_result(self):
        """One broken task must not discard the work of the others."""
        context = make_context(2)
        OperationSubagentsLayer(StubSubagentFactory(fail = True), make_pool()).execute(context)
        assert [r.status for r in context.results] == ["error", "error"]

    def test_a_failure_still_returns_the_slot(self):
        pool = make_pool(2)
        OperationSubagentsLayer(StubSubagentFactory(fail = True), pool).execute(make_context(2))
        assert pool.available == 2

    def test_every_task_in_a_run_gets_the_same_workspace(self):
        factory = StubSubagentFactory()
        OperationSubagentsLayer(factory, make_pool()).execute(make_context(2))
        roots = {env.root for env in factory.envs}
        assert len(roots) == 1

    def test_no_tasks_produces_no_results(self):
        context = make_context(0)
        OperationSubagentsLayer(StubSubagentFactory(), make_pool()).execute(context)
        assert context.results == []

    def test_sandbox_leases_are_reported(self):
        tracer = TracingService()
        OperationSubagentsLayer(StubSubagentFactory(), make_pool(), tracer).execute(make_context(2))
        acquired = [e for e in tracer.events() if e.type is TraceEventType.SANDBOX_ACQUIRED]
        released = [e for e in tracer.events() if e.type is TraceEventType.SANDBOX_RELEASED]
        assert len(acquired) == 2 and len(released) == 2

    def test_each_subagent_is_reported_with_its_type(self):
        tracer = TracingService()
        OperationSubagentsLayer(StubSubagentFactory(), make_pool(), tracer).execute(make_context(2))
        started = [e for e in tracer.events() if e.type is TraceEventType.SUBAGENT_STARTED]
        assert [e.label for e in started] == ["CODE", "CODE"]
