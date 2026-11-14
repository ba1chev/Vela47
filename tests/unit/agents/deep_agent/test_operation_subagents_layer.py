import pytest
import pathlib
import tempfile

from app.intelligence.messages import MessageAI
from app.intelligence.tools import ToolWriteFile
from app.intelligence.agents import OperationTask
from app.intelligence.agents import OperationType
from app.intelligence.messages import MessageHuman
from app.intelligence.tracing import TracingService
from app.intelligence.tracing import TraceEventType
from app.intelligence.agents import OperationContext
from app.intelligence.messages import MessageToolCall
from app.intelligence.agents import A2AInteractionType
from app.intelligence.sandbox import SandboxPoolInMemory
from app.intelligence.agents import OperationSubagentType
from app.intelligence.agents import OperationSubagentsLayer
from app.intelligence.agents import OperationSubagentFactory
from app.intelligence.agents import OperationSubagentPeering
from app.intelligence.agents import OperationSubagentBlueprint
from app.intelligence.middleware import MiddlewareSlidingWindow
from tests.fixtures.sandbox.named_sandbox_pool import NamedSandboxPool
from tests.fixtures.model.scripted_tool_model import ScriptedToolModel
from tests.fixtures.agents.stub_subagent_factory import StubSubagentFactory
from tests.fixtures.agents.recording_a2a_interaction_factory import RecordingA2AInteractionFactory


def make_context(count = 2):
    return OperationContext(
        goal = MessageHuman(content = "goal"),
        tasks = [OperationTask(id = f"t{i}", step_index = i,
            subagent_type = OperationSubagentType.CODE,
            instruction = f"task {i}") for i in range(count)])


def make_pool(size = 3):
    return SandboxPoolInMemory(size = size, base_directory = pathlib.Path(tempfile.mkdtemp()))


def make_typed_context(*types):
    return OperationContext(
        goal = MessageHuman(content = "goal"),
        tasks = [OperationTask(id = f"t{i}", step_index = i, subagent_type = current_type,
            instruction = f"task {i}") for i, current_type in enumerate(types)])


def make_peering(interaction_type = A2AInteractionType.HOST, max_messages = 2):
    return OperationSubagentPeering(
        interaction_type = interaction_type,
        peers = {OperationSubagentType.TEST: OperationSubagentType.CODE, OperationSubagentType.REVIEW: OperationSubagentType.CODE},
        max_messages = max_messages
    )


def make_peered_layer(factory, pool = None, tracer = None, interaction_type = A2AInteractionType.HOST,
    interaction_factory = None, max_messages = 2):
    return OperationSubagentsLayer(
        factory, pool if pool is not None else make_pool(), tracer,
        peering = make_peering(interaction_type, max_messages),
        interaction_factory = interaction_factory
    )


def call(name, args, id):
    return MessageAI(content = "", tool_calls = [MessageToolCall(name = name, args = args, id = id)])


def make_blueprint(model, tool_factories):
    return OperationSubagentBlueprint(
        tool_factories = tool_factories,
        prompt_template = "You are a worker. Your tools are {tools}.",
        model = model,
        max_context_window_size = 24,
        context_window_middleware = MiddlewareSlidingWindow(step = 2),
        max_iterations = 4
    )


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

    def test_the_subagent_is_told_the_users_goal_with_its_instruction(self):
        context = OperationContext(
            goal = MessageHuman(content = "plan the Amusnet hackathon"),
            tasks = [OperationTask(id = "t0", step_index = 0, subagent_type = OperationSubagentType.RESEARCH,
                instruction = "find the dates of the hackathon", goal = "plan the Amusnet hackathon")]
        )
        OperationSubagentsLayer(StubSubagentFactory(), make_pool()).execute(context)
        content = context.results[0].content
        assert "Your task: find the dates of the hackathon" in content and "plan the Amusnet hackathon" in content

    def test_a_task_without_a_goal_is_handed_its_instruction_alone(self):
        context = make_context(1)
        OperationSubagentsLayer(StubSubagentFactory(), make_pool()).execute(context)
        assert context.results[0].content == "did task 0"

    def test_the_evidence_of_a_step_travels_with_its_result(self):
        context = make_context(1)
        OperationSubagentsLayer(StubSubagentFactory(), make_pool()).execute(context)
        assert context.results[0].evidence == ["checked by a stub"]

    def test_a_failed_step_carries_no_evidence(self):
        context = make_context(1)
        OperationSubagentsLayer(StubSubagentFactory(fail = True), make_pool()).execute(context)
        assert context.results[0].evidence == []


class TestOperationSubagentsLayerPeering:
    def test_without_a_peering_no_subagent_is_given_a_peer(self):
        factory = StubSubagentFactory()
        OperationSubagentsLayer(factory, make_pool()).execute(make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST))
        assert factory.peer_tools == [None, None]

    def test_a_tester_after_a_coder_can_message_it(self):
        factory = StubSubagentFactory()
        make_peered_layer(factory).execute(make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST))
        assert factory.peer_tools[0] is None
        assert factory.peer_tools[1].name == "message_worker" and factory.peer_tools[1].peer_name == "CODE"

    def test_a_reviewer_after_a_coder_can_message_it(self):
        factory = StubSubagentFactory()
        make_peered_layer(factory).execute(make_typed_context(OperationSubagentType.CODE, OperationSubagentType.REVIEW))
        assert factory.peer_tools[1] is not None

    def test_nobody_is_given_a_peer_before_a_coder_has_run(self):
        factory = StubSubagentFactory()
        make_peered_layer(factory).execute(make_typed_context(OperationSubagentType.REVIEW, OperationSubagentType.RESEARCH))
        assert factory.peer_tools == [None, None]

    def test_a_type_without_a_peer_is_never_given_one(self):
        factory = StubSubagentFactory()
        make_peered_layer(factory).execute(make_typed_context(OperationSubagentType.CODE, OperationSubagentType.RESEARCH))
        assert factory.peer_tools == [None, None]

    def test_a_failed_coder_cannot_be_messaged(self):
        factory = StubSubagentFactory(fail_types = [OperationSubagentType.CODE])
        make_peered_layer(factory).execute(make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST))
        assert factory.peer_tools == [None, None]

    def test_the_message_reaches_the_coder_and_its_answer_comes_back(self):
        factory = StubSubagentFactory(peer_messages = ["f(2) returns 5, expected 4"])
        make_peered_layer(factory).execute(make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST))
        coder, tester = factory.agents
        assert "The TEST worker checking the code you wrote sends you this:\n\nf(2) returns 5, expected 4" in coder.received[1]
        assert tester.answers[0].startswith("The CODE worker answered:\ndid The TEST worker")

    def test_the_coder_keeps_its_slot_until_the_layer_ends(self):
        pool = make_pool(2)
        layer = make_peered_layer(StubSubagentFactory(), pool)
        context = make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST)
        layer.execute(context)
        assert [r.status for r in context.results] == ["success", "success"] and pool.available == 2

    def test_a_coder_holding_the_last_slot_is_let_go_for_the_next_step(self):
        """Keeping the coder alive must never cost a run a step it could run before."""
        pool = make_pool(1)
        factory = StubSubagentFactory()
        context = make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST)
        make_peered_layer(factory, pool).execute(context)
        assert [r.status for r in context.results] == ["success", "success"]
        assert factory.peer_tools == [None, None] and pool.available == 1

    def test_a_full_pool_without_a_kept_coder_still_raises(self):
        pool = make_pool(1)
        pool.acquire()
        with pytest.raises(RuntimeError, match = "No sandbox slot available"):
            make_peered_layer(StubSubagentFactory(), pool).execute(make_typed_context(OperationSubagentType.TEST))

    def test_a_newer_coder_replaces_the_older_one_and_frees_its_slot(self):
        pool = make_pool(2)
        factory = StubSubagentFactory(peer_messages = ["bug"])
        context = make_typed_context(OperationSubagentType.CODE, OperationSubagentType.CODE, OperationSubagentType.TEST)
        make_peered_layer(factory, pool).execute(context)
        first, second, tester = factory.agents
        assert [r.status for r in context.results] == ["success", "success", "success"]
        assert len(first.received) == 1 and len(second.received) == 2 and pool.available == 2

    def test_the_interaction_connects_on_the_first_message_and_closes_after_the_step(self):
        interactions = RecordingA2AInteractionFactory()
        make_peered_layer(StubSubagentFactory(peer_messages = ["bug", "another"]), interaction_factory = interactions).execute(
            make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST))
        assert interactions.interactions[0].events == ["connect", "disconnect"]
        assert len(interactions.interactions[0].transfers) == 4

    def test_a_step_that_sends_nothing_never_connects(self):
        interactions = RecordingA2AInteractionFactory()
        make_peered_layer(StubSubagentFactory(), interaction_factory = interactions).execute(
            make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST))
        assert interactions.interactions[0].events == []

    def test_a_docker_interaction_connects_the_two_slots_containers(self):
        interactions = RecordingA2AInteractionFactory()
        make_peered_layer(StubSubagentFactory(), NamedSandboxPool(size = 3, base_directory = pathlib.Path(tempfile.mkdtemp())),
            interaction_type = A2AInteractionType.DOCKER, interaction_factory = interactions).execute(
            make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST))
        assert interactions.created == [
            (A2AInteractionType.DOCKER, {"left_container": "vela47-slot-0", "right_container": "vela47-slot-1"})
        ]

    def test_a_host_interaction_is_given_no_containers(self):
        interactions = RecordingA2AInteractionFactory()
        make_peered_layer(StubSubagentFactory(), interaction_factory = interactions).execute(
            make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST))
        assert interactions.created == [(A2AInteractionType.HOST, {})]

    def test_the_messages_are_capped_per_step(self):
        factory = StubSubagentFactory(peer_messages = ["one", "two", "three"])
        make_peered_layer(factory, max_messages = 2).execute(make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST))
        coder, tester = factory.agents
        assert len(coder.received) == 3 and "the most one step may send" in tester.answers[2]

    def test_an_exchange_is_recorded_as_evidence(self):
        context = make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST)
        make_peered_layer(StubSubagentFactory(peer_messages = ["bug"])).execute(context)
        assert context.results[1].evidence == [
            "checked by a stub",
            "The system carried 1 message(s) from this step to the CODE worker and its answer(s) back."
        ]

    def test_a_step_that_sent_nothing_adds_no_evidence(self):
        context = make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST)
        make_peered_layer(StubSubagentFactory()).execute(context)
        assert context.results[1].evidence == ["checked by a stub"]

    def test_every_exchange_is_traced_with_its_direction(self):
        tracer = TracingService()
        make_peered_layer(StubSubagentFactory(peer_messages = ["bug"]), tracer = tracer).execute(
            make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST))
        started = [e for e in tracer.events() if e.type is TraceEventType.A2A_STARTED]
        finished = [e for e in tracer.events() if e.type is TraceEventType.A2A_FINISHED]
        assert [e.label for e in started] == ["TEST → CODE"] and started[0].payload["message"] == "bug"
        assert finished[0].payload["status"] == "success" and finished[0].payload["interaction"] == "host"

    def test_a_connection_that_fails_is_traced_and_every_slot_still_returns(self):
        tracer = TracingService()
        pool = make_pool(2)
        context = make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST)
        make_peered_layer(StubSubagentFactory(peer_messages = ["bug"]), pool, tracer,
            interaction_factory = RecordingA2AInteractionFactory(fail_connect = True)).execute(context)
        finished = [e for e in tracer.events() if e.type is TraceEventType.A2A_FINISHED]
        assert finished[0].payload["status"] == "error" and "no network for the pair" in finished[0].payload["result"]
        assert context.results[1].status == "error" and pool.available == 2

    def test_real_subagents_fix_a_bug_through_the_interaction(self):
        """A coder writes a wrong file, the tester messages it, and the coder fixes the
        file in the run's workspace before the tester writes its report."""
        coder_model = ScriptedToolModel([
            call("write_file", {"path": "units.py", "content": "def double(x):\n    return x + 2\n"}, "c1"),
            MessageAI(content = "Wrote units.py with double(x)."),
            call("write_file", {"path": "units.py", "content": "def double(x):\n    return x * 2\n"}, "c2"),
            MessageAI(content = "Changed double to return x * 2.")
        ])
        tester_model = ScriptedToolModel([
            call("message_worker", {"message": "double(3) returns 5, expected 6 (units.py)"}, "t1"),
            MessageAI(content = "The coder fixed double; it now returns x * 2.")
        ])
        factory = OperationSubagentFactory({
            OperationSubagentType.CODE: make_blueprint(coder_model, [ToolWriteFile]),
            OperationSubagentType.TEST: make_blueprint(tester_model, [])
        })
        pool = make_pool(2)
        context = make_typed_context(OperationSubagentType.CODE, OperationSubagentType.TEST)
        make_peered_layer(factory, pool).execute(context)

        assert (pool.base_directory / context.run_id / "units.py").read_text() == "def double(x):\n    return x * 2\n"
        assert [r.status for r in context.results] == ["success", "success"]
        assert context.results[1].content == "The coder fixed double; it now returns x * 2."
        assert "1 message(s)" in context.results[1].evidence[0]
        tester_tools = [current["function"]["name"] for current in tester_model.calls[0][1]]
        assert tester_tools == ["message_worker"]
        assert "The worker who wrote the code" in tester_model.calls[0][0][0].content
        tool_result = tester_model.calls[1][0][-1]
        assert tool_result.status == "success" and "Changed double to return x * 2." in tool_result.content
