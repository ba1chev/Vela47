import pytest
import pathlib
import tempfile

from app.intelligence.tools import ToolReadFile
from app.intelligence.tools import ToolWriteFile
from app.intelligence.tools import ToolMessageWorker
from app.intelligence.sandbox import SandboxEnvLocal
from tests.fixtures.model.fake_model import FakeModel
from app.intelligence.agents import OperationSubagentType
from app.intelligence.agents import OperationSubagentFactory
from app.intelligence.agents import OperationSubagentBlueprint
from app.intelligence.middleware import MiddlewareSlidingWindow
from tests.fixtures.agents.recording_probe import RecordingProbe


def make_factory(prompt = "You write code. Your tools are {tools}.", probe_factories = None):
    blueprint = OperationSubagentBlueprint(
        tool_factories = [ToolReadFile, ToolWriteFile],
        probe_factories = probe_factories,
        prompt_template = prompt,
        model = FakeModel(),
        max_context_window_size = 8,
        context_window_middleware = MiddlewareSlidingWindow(step = 2),
        max_iterations = 2
    )
    return OperationSubagentFactory({OperationSubagentType.CODE: blueprint})


def make_env():
    return SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / "run")


class TestOperationSubagentFactory:
    def test_it_builds_an_agent_for_a_known_type(self):
        agent = make_factory().create(OperationSubagentType.CODE, make_env())
        assert agent is not None

    def test_an_unregistered_type_is_refused(self):
        with pytest.raises(ValueError, match = "No blueprint registered"):
            make_factory().create(OperationSubagentType.REVIEW, make_env())

    def test_every_tool_is_bound_to_the_env_it_was_given(self):
        env = make_env()
        agent = make_factory().create(OperationSubagentType.CODE, env)
        assert agent._tool_registry.get("write_file")._sandbox_env is env
        assert agent._tool_registry.get("read_file")._sandbox_env is env

    def test_each_call_binds_its_own_env(self):
        factory = make_factory()
        first_env, second_env = make_env(), make_env()
        first = factory.create(OperationSubagentType.CODE, first_env)
        second = factory.create(OperationSubagentType.CODE, second_env)
        assert first._tool_registry.get("write_file")._sandbox_env is first_env
        assert second._tool_registry.get("write_file")._sandbox_env is second_env

    def test_each_agent_starts_with_empty_memory(self):
        factory = make_factory()
        agent = factory.create(OperationSubagentType.CODE, make_env())
        assert len(agent._short_term_memory) == 0

    def test_the_whole_toolset_is_registered(self):
        agent = make_factory().create(OperationSubagentType.CODE, make_env())
        assert [current.name for current in agent._tool_registry.all()] == ["read_file", "write_file"]

    def test_the_prompt_is_told_the_tool_names(self):
        agent = make_factory().create(OperationSubagentType.CODE, make_env())
        prompt = agent._prompt_manager.build_system_messages()[0].content
        assert "Your tools are read_file, write_file." in prompt and "{tools}" not in prompt

    def test_contains_reports_what_is_registered(self):
        factory = make_factory()
        assert OperationSubagentType.CODE in factory
        assert OperationSubagentType.TEST not in factory

    def test_each_task_gets_probes_bound_to_its_own_sandbox(self):
        factory = make_factory(probe_factories = [RecordingProbe])
        first, second = make_env(), SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / "run", identifier = "other")
        assert factory.create(OperationSubagentType.CODE, first)._probes[0]._sandbox_env is first
        assert factory.create(OperationSubagentType.CODE, second)._probes[0]._sandbox_env is second

    def test_a_peer_tool_joins_the_toolset(self):
        peer_tool = ToolMessageWorker(lambda message: "ok", "CODE")
        agent = make_factory().create(OperationSubagentType.CODE, make_env(), peer_tool = peer_tool)
        assert [current.name for current in agent._tool_registry.all()] == ["read_file", "write_file", "message_worker"]
        assert agent._tool_registry.get("message_worker") is peer_tool

    def test_a_peer_tool_tells_the_prompt_who_it_reaches_and_how_often(self):
        peer_tool = ToolMessageWorker(lambda message: "ok", "CODE", max_messages = 3)
        agent = make_factory().create(OperationSubagentType.CODE, make_env(), peer_tool = peer_tool)
        prompt = agent._prompt_manager.build_system_messages()[0].content
        assert "Your tools are read_file, write_file, message_worker." in prompt
        assert "The CODE worker that wrote the code" in prompt and "at most 3 messages" in prompt

    def test_without_a_peer_tool_the_prompt_says_nothing_of_one(self):
        prompt = make_factory().create(OperationSubagentType.CODE, make_env())._prompt_manager.build_system_messages()[0].content
        assert "message_worker" not in prompt and "The worker who wrote the code" not in prompt
