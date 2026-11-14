from typing import Callable

from app.server.builders import KEEP_ALIVE
from app.intelligence.tools import ToolBase
from app.intelligence.web import WebFetcher
from app.intelligence.agents import DeepAgent
from app.intelligence.model import ModelConfig
from app.intelligence.tools import ToolFetchUrl
from app.intelligence.tools import ToolReadFile
from app.intelligence.tools import ToolEditFile
from app.intelligence.tools import ToolRunTests
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.tools import ToolListFiles
from app.intelligence.tools import ToolWebSearch
from app.intelligence.tools import ToolWriteFile
from app.intelligence.tools import ToolWriteTest
from app.intelligence.agents import PromptManager
from app.intelligence.memory import VectorDbMemory
from app.intelligence.model import ModelFoundation
from app.intelligence.tools import ToolSearchFiles
from app.intelligence.web import WebSearchDuckDuckGo
from app.intelligence.sandbox import SandboxPoolBase
from app.intelligence.agents import OperationPipeline
from app.server.builders import CONTEXT_WINDOW_TOKENS
from app.intelligence.agents import A2AInteractionType
from app.intelligence.tools import ToolSearchDocuments
from app.server.builders import build_knowledge_memory
from app.intelligence.sandbox import SandboxPoolDocker
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.agents import OperationPolicyFull
from app.intelligence.agents import OperationSubagentType
from app.server.config_environment import ConfigEnvironment
from app.intelligence.agents import OperationSubagentFactory
from app.intelligence.agents import OperationSubagentPeering
from app.intelligence.agents import OperationSubagentBlueprint
from app.intelligence.middleware import MiddlewareSlidingWindow
from app.intelligence.agents import OperationSubagentProbeTests
from app.intelligence.agents import OperationSubagentProbeSources
from app.intelligence.agents import OperationSubagentProbeWorkspace
from app.intelligence.agents import SUBAGENT_SYSTEM_PROMPT_TEMPLATES

MODEL_NAMES = {
    ConfigEnvironment.DEV: "qwen3.5:9b",
    ConfigEnvironment.PROD: "qwen3.5:35b-a3b"
}
SUBAGENT_MAX_ITERATIONS = 6
SUBAGENT_PROBE_FACTORIES = {
    OperationSubagentType.RESEARCH: [OperationSubagentProbeSources],
    OperationSubagentType.CODE: [OperationSubagentProbeWorkspace],
    OperationSubagentType.TEST: [OperationSubagentProbeWorkspace, OperationSubagentProbeTests],
    OperationSubagentType.REVIEW: []
}
SUBAGENT_PEERS = {
    OperationSubagentType.TEST: OperationSubagentType.CODE,
    OperationSubagentType.REVIEW: OperationSubagentType.CODE
}
SUBAGENT_MAX_PEER_MESSAGES = 2


def subagent_tool_factories(knowledge_memory: VectorDbMemory,
    web_fetcher: WebFetcher) -> dict[OperationSubagentType, list[Callable[[SandboxEnv], ToolBase]]]:
    web_search = WebSearchDuckDuckGo(web_fetcher)
    document_search = [lambda sandbox_env: ToolSearchDocuments(knowledge_memory)] if len(knowledge_memory) > 0 else []
    return {
        OperationSubagentType.RESEARCH: [
            *document_search,
            ToolSearchFiles,
            lambda sandbox_env: ToolWebSearch(web_search),
            lambda sandbox_env: ToolFetchUrl(web_fetcher)
        ],
        OperationSubagentType.CODE: [ToolListFiles, ToolReadFile, ToolWriteFile, ToolEditFile],
        OperationSubagentType.TEST: [ToolListFiles, ToolReadFile, ToolWriteTest, ToolRunTests],
        OperationSubagentType.REVIEW: [ToolListFiles, ToolReadFile, ToolSearchFiles]
    }


def subagent_peering(sandbox_pool: SandboxPoolBase) -> OperationSubagentPeering:
    return OperationSubagentPeering(
        interaction_type = (
            A2AInteractionType.DOCKER
            if isinstance(sandbox_pool, SandboxPoolDocker)
            else A2AInteractionType.HOST
        ),
        peers = SUBAGENT_PEERS,
        max_messages = SUBAGENT_MAX_PEER_MESSAGES
    )


def build_deep_agent(tracing_service: TracingServiceBase, sandbox_pool: SandboxPoolBase,
    web_fetcher: WebFetcher, knowledge_entries: list[VectorDbMemoryEntry],
    environment: ConfigEnvironment) -> DeepAgent:
    model_name = MODEL_NAMES[environment]
    context_window_tokens = CONTEXT_WINDOW_TOKENS[environment]
    keep_alive = KEEP_ALIVE[environment]
    planning_model = ModelFoundation(
        ModelConfig(
            model_name = model_name, temperature = 0.1, think = False,
            context_window_tokens = context_window_tokens, keep_alive = keep_alive
        ),
        tracing_service
    )
    merging_model = ModelFoundation(
        ModelConfig(
            model_name = model_name, temperature = 0.6,
            context_window_tokens = context_window_tokens, keep_alive = keep_alive
        ),
        tracing_service
    )

    tool_factories = subagent_tool_factories(
        build_knowledge_memory(tracing_service, knowledge_entries, environment), web_fetcher
    )
    blueprints = {
        current_type: OperationSubagentBlueprint(
            tool_factories = tool_factories[current_type],
            prompt_template = SUBAGENT_SYSTEM_PROMPT_TEMPLATES[current_type],
            model = ModelFoundation(
                ModelConfig(
                    model_name = model_name, temperature = 0.3,
                    context_window_tokens = context_window_tokens, keep_alive = keep_alive
                ),
                tracing_service
            ),
            max_context_window_size = 4 * SUBAGENT_MAX_ITERATIONS,
            context_window_middleware = MiddlewareSlidingWindow(step = 2),
            max_iterations = SUBAGENT_MAX_ITERATIONS,
            probe_factories = SUBAGENT_PROBE_FACTORIES[current_type]
        )
        for current_type in OperationSubagentType
    }

    policy = OperationPolicyFull(
        planning_model = planning_model,
        merging_model = merging_model,
        subagent_factory = OperationSubagentFactory(blueprints, tracing_service),
        sandbox_pool = sandbox_pool,
        tracing_service = tracing_service,
        subagent_peering = subagent_peering(sandbox_pool)
    )

    return DeepAgent(
        model = merging_model,
        prompt_manager = PromptManager(),
        max_context_window_size = 8,
        operation_pipeline = OperationPipeline(policy, tracing_service),
        tracing_service = tracing_service
    )
