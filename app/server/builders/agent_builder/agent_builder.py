from typing import Callable

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
from app.intelligence.tools import ToolSearchDocuments
from app.server.builders import build_knowledge_memory
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.agents import OperationPolicyFull
from app.intelligence.agents import OperationSubagentType
from app.intelligence.agents import OperationSubagentFactory
from app.intelligence.agents import OperationSubagentBlueprint
from app.intelligence.middleware import MiddlewareSlidingWindow
from app.intelligence.agents import SUBAGENT_SYSTEM_PROMPT_TEMPLATES

MODEL_NAME = "qwen3:1.7b"
SUBAGENT_MAX_ITERATIONS = 6


def subagent_tool_factories(knowledge_memory: VectorDbMemory,
    web_fetcher: WebFetcher) -> dict[OperationSubagentType, list[Callable[[SandboxEnv], ToolBase]]]:
    """The toolset of each subagent type — small on purpose, three or four tools that
    together let a step do its job and check it.

    RESEARCH gathers: the user's documents, the workspace, the web and the pages found
    there. CODE looks before it writes and edits rather than rewrites. TEST writes tests
    and runs them in the sandbox, so it learns whether they pass. REVIEW only reads.

    search_documents is offered only when the user has documents to search. Over an
    empty store its only answer is that there is nothing there, and a small model
    reports that as its finding instead of moving on to the web.

    Every value is a factory, because a tool acts on the sandbox its agent is leased
    and that lease does not exist until a task is dispatched. The tools that need
    something else — the owner's documents, the web — are closures over it that ignore
    the sandbox they are handed."""
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


def build_deep_agent(tracing_service: TracingServiceBase, sandbox_pool: SandboxPoolBase,
    web_fetcher: WebFetcher, knowledge_entries: list[VectorDbMemoryEntry]) -> DeepAgent:
    """Assembles a complete DeepAgent wired to one run's tracer.

    Models and agents are built per request rather than once at startup, which is what
    keeps a tracer scoped to a single run: a model built with this run's tracer can
    only ever report into this run. Rebuilding is nearly free — models hold a config,
    not a connection — and it also guarantees each run starts from empty memory.

    The sandbox pool and the web fetcher are the exceptions and are passed in. The
    pool's containers are started once for the whole process, so rebuilding it per
    request would mean paying tens of seconds of container startup on every message.
    The caller's documents arrive already embedded, loaded by the route for this owner
    only, and are searched the way the RAG agent searches them.

    The DeepAgent keeps the last eight messages of a conversation as history. A small
    model's context has to hold the planning schema as well, and a long chat would
    otherwise push that out of it.

    Every model shares the RAG agent's context size. Ollama reloads a model whenever the
    context size it is asked for changes, so one size for every call keeps a single
    loaded copy serving planning, every subagent and merging. The subagents' windows
    hold a whole task — the instruction and every turn of its loop — because a sliding
    window that overflowed would drop the instruction first.

    The planning model is pinned to a low temperature because its output must satisfy a
    JSON schema, while merging is left free to write prose."""
    planning_model = ModelFoundation(
        ModelConfig(model_name = MODEL_NAME, temperature = 0.1, think = False, context_window_tokens = CONTEXT_WINDOW_TOKENS),
        tracing_service
    )
    merging_model = ModelFoundation(
        ModelConfig(model_name = MODEL_NAME, temperature = 0.6, context_window_tokens = CONTEXT_WINDOW_TOKENS),
        tracing_service
    )

    tool_factories = subagent_tool_factories(
        build_knowledge_memory(tracing_service, knowledge_entries), web_fetcher
    )
    blueprints = {
        current_type: OperationSubagentBlueprint(
            tool_factories = tool_factories[current_type],
            prompt_template = SUBAGENT_SYSTEM_PROMPT_TEMPLATES[current_type],
            model = ModelFoundation(
                ModelConfig(model_name = MODEL_NAME, temperature = 0.3, context_window_tokens = CONTEXT_WINDOW_TOKENS),
                tracing_service
            ),
            max_context_window_size = 4 * SUBAGENT_MAX_ITERATIONS,
            context_window_middleware = MiddlewareSlidingWindow(step = 2),
            max_iterations = SUBAGENT_MAX_ITERATIONS
        )
        for current_type in OperationSubagentType
    }

    policy = OperationPolicyFull(
        planning_model = planning_model,
        merging_model = merging_model,
        subagent_factory = OperationSubagentFactory(blueprints, tracing_service),
        sandbox_pool = sandbox_pool,
        tracing_service = tracing_service
    )

    return DeepAgent(
        model = merging_model,
        prompt_manager = PromptManager(),
        max_context_window_size = 8,
        operation_pipeline = OperationPipeline(policy, tracing_service),
        tracing_service = tracing_service
    )
