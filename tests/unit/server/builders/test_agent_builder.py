import pathlib
import tempfile

from app.server.builders import KEEP_ALIVE
from app.intelligence.web import WebFetcher
from app.server.builders import MODEL_NAMES
from app.intelligence.agents import DeepAgent
from app.server.builders import SUBAGENT_PEERS
from app.server.builders import build_deep_agent
from app.server.builders import subagent_peering
from app.intelligence.messages import MessageType
from app.intelligence.memory import VectorDbMemory
from app.intelligence.sandbox import SandboxEnvLocal
from app.server.builders import CONTEXT_WINDOW_TOKENS
from app.intelligence.agents import A2AInteractionType
from app.intelligence.sandbox import SandboxPoolDocker
from app.intelligence.tracing import TracingServiceNull
from app.server.builders import subagent_tool_factories
from app.intelligence.sandbox import SandboxPoolInMemory
from app.server.builders import SUBAGENT_PROBE_FACTORIES
from app.intelligence.agents import OperationSubagentType
from app.server.config_environment import ConfigEnvironment
from tests.fixtures.model.fake_embeddings import FakeEmbeddings
from app.intelligence.agents import SUBAGENT_SYSTEM_PROMPT_TEMPLATES
from tests.fixtures.sandbox.named_sandbox_pool import NamedSandboxPool


def make_toolsets(with_documents = True):
    env = SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / "run")
    memory = VectorDbMemory(FakeEmbeddings())
    if with_documents:
        memory.append_message("Backups run nightly at two in the morning.", MessageType.SYSTEM_MESSAGE)
    factories = subagent_tool_factories(memory, WebFetcher())
    return {
        current_type: [current_factory(env) for current_factory in factories[current_type]]
        for current_type in OperationSubagentType
    }


def names(tools):
    return [current.name for current in tools]


class TestAgentBuilder:
    def test_each_type_gets_its_small_toolset(self):
        toolsets = make_toolsets()
        assert names(toolsets[OperationSubagentType.RESEARCH]) == ["search_documents", "search_files", "web_search", "fetch_url"]
        assert names(toolsets[OperationSubagentType.CODE]) == ["list_files", "read_file", "write_file", "edit_file"]
        assert names(toolsets[OperationSubagentType.TEST]) == ["list_files", "read_file", "write_test", "run_tests"]
        assert names(toolsets[OperationSubagentType.REVIEW]) == ["list_files", "read_file", "search_files"]

    def test_research_is_not_offered_document_search_without_documents(self):
        assert names(make_toolsets(with_documents = False)[OperationSubagentType.RESEARCH]) == ["search_files", "web_search", "fetch_url"]

    def test_only_review_and_research_are_read_only(self):
        writers = {"write_file", "edit_file", "write_test", "run_tests"}
        toolsets = make_toolsets()
        assert not writers & set(names(toolsets[OperationSubagentType.REVIEW]))
        assert not writers & set(names(toolsets[OperationSubagentType.RESEARCH]))

    def test_a_prompt_only_names_tools_its_type_has(self):
        every_name = {current.name for current_tools in make_toolsets().values() for current in current_tools}
        for with_documents in (True, False):
            for current_type, current_tools in make_toolsets(with_documents).items():
                mentioned = {current for current in every_name if current in SUBAGENT_SYSTEM_PROMPT_TEMPLATES[current_type]}
                assert mentioned <= set(names(current_tools)), (current_type, with_documents)

    def test_a_tool_only_points_to_tools_in_the_same_toolset(self):
        toolsets = make_toolsets()
        every_name = {current.name for current_tools in toolsets.values() for current in current_tools}
        for current_type, current_tools in toolsets.items():
            for current_tool in current_tools:
                mentioned = {current for current in every_name - {current_tool.name} if current in current_tool.description}
                assert mentioned <= set(names(current_tools)), (current_type, current_tool.name)

    def test_the_deep_agent_is_assembled_without_contacting_anything(self):
        agent = build_deep_agent(TracingServiceNull(), SandboxPoolInMemory(size = 1), WebFetcher(), [], ConfigEnvironment.DEV)
        assert isinstance(agent, DeepAgent)

    def test_each_type_is_checked_by_the_probes_its_work_calls_for(self):
        names = {current_type: [current.__name__ for current in SUBAGENT_PROBE_FACTORIES[current_type]] for current_type in OperationSubagentType}
        assert names == {
            OperationSubagentType.RESEARCH: ["OperationSubagentProbeSources"],
            OperationSubagentType.CODE: ["OperationSubagentProbeWorkspace"],
            OperationSubagentType.TEST: ["OperationSubagentProbeWorkspace", "OperationSubagentProbeTests"],
            OperationSubagentType.REVIEW: []
        }

    def test_testers_and_reviewers_can_message_the_coder(self):
        assert SUBAGENT_PEERS == {
            OperationSubagentType.TEST: OperationSubagentType.CODE,
            OperationSubagentType.REVIEW: OperationSubagentType.CODE
        }

    def test_without_containers_the_messages_stay_in_the_process(self):
        assert subagent_peering(SandboxPoolInMemory(size = 1)).interaction_type is A2AInteractionType.HOST
        assert subagent_peering(NamedSandboxPool(size = 1)).interaction_type is A2AInteractionType.HOST

    def test_with_containers_the_messages_cross_them(self):
        pool = SandboxPoolDocker(pathlib.Path(tempfile.mkdtemp()) / "docker-compose.yaml")
        assert subagent_peering(pool).interaction_type is A2AInteractionType.DOCKER

    def test_no_prompt_names_the_peer_tool_it_is_only_given_with(self):
        for current_type in OperationSubagentType:
            assert "message_worker" not in SUBAGENT_SYSTEM_PROMPT_TEMPLATES[current_type]

    def test_the_deep_agent_lets_its_subagents_message_each_other(self):
        agent = build_deep_agent(TracingServiceNull(), SandboxPoolInMemory(size = 1), WebFetcher(), [], ConfigEnvironment.DEV)
        layer = next(current for current in agent._operation_pipeline._operation_layers if current.operation_type.name == "SUBAGENTS")
        assert layer._peering.peers == SUBAGENT_PEERS

    def test_every_environment_has_a_model(self):
        assert set(MODEL_NAMES) == set(ConfigEnvironment)

    def test_the_deep_agent_runs_on_the_model_of_its_environment(self):
        for current_environment in ConfigEnvironment:
            agent = build_deep_agent(TracingServiceNull(), SandboxPoolInMemory(size = 1), WebFetcher(), [], current_environment)
            assert agent._model._config.model_name == MODEL_NAMES[current_environment]
            assert agent._model._config.context_window_tokens == CONTEXT_WINDOW_TOKENS[current_environment]
            assert agent._model._config.keep_alive == KEEP_ALIVE[current_environment]
