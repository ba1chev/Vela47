from app.intelligence.model import ModelConfig
from app.intelligence.agents import DeepAgent
from app.intelligence.agents import PromptManager
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.model import ModelFoundation
from app.intelligence.tools import ToolReadFile
from app.intelligence.tools import ToolWriteFile
from app.intelligence.tools import ToolWriteTest
from app.intelligence.tools import ToolSearchFiles
from app.intelligence.middleware import MiddlewareSlidingWindow
from app.intelligence.agents import OperationPipeline
from app.intelligence.agents import SUBAGENT_SYSTEM_PROMPT_TEMPLATES
from app.intelligence.agents import OperationPolicyFull
from app.intelligence.sandbox import SandboxPoolBase
from app.intelligence.agents import OperationSubagentType
from app.intelligence.agents import OperationSubagentBlueprint
from app.intelligence.agents import OperationSubagentFactory

MODEL_NAME = "qwen3:1.7b"

# One tool per type, matching the single responsibility each prompt describes. The
# values are factories, not tools: a tool acts on the sandbox its agent is leased,
# which does not exist until a task is dispatched.
SUBAGENT_TOOL_FACTORIES = {
    OperationSubagentType.RESEARCH: ToolSearchFiles,
    OperationSubagentType.CODE: ToolWriteFile,
    OperationSubagentType.TEST: ToolWriteTest,
    OperationSubagentType.REVIEW: ToolReadFile,
}


def build_deep_agent(tracing_service: TracingServiceBase,
    sandbox_pool: SandboxPoolBase) -> DeepAgent:
    """Assembles a complete DeepAgent wired to one run's tracer.

    Models and agents are built per request rather than once at startup, which is what
    keeps a tracer scoped to a single run: a model built with this run's tracer can
    only ever report into this run. Rebuilding is nearly free — models hold a config,
    not a connection — and it also guarantees each run starts from empty memory.

    The sandbox pool is the exception and is passed in. Its containers are started
    once for the whole process, so rebuilding it per request would mean paying tens
    of seconds of container startup on every message.

    The three models are separate instances on purpose. Planning is pinned to a low
    temperature because its output must satisfy a JSON schema, while merging is left
    free to write prose."""
    planning_model = ModelFoundation(
        ModelConfig(model_name = MODEL_NAME, temperature = 0.1, think = False),
        tracing_service
    )
    merging_model = ModelFoundation(
        ModelConfig(model_name = MODEL_NAME, temperature = 0.6),
        tracing_service
    )

    blueprints = {
        current_type: OperationSubagentBlueprint(
            tool_factory = SUBAGENT_TOOL_FACTORIES[current_type],
            prompt_template = SUBAGENT_SYSTEM_PROMPT_TEMPLATES[current_type],
            model = ModelFoundation(
                ModelConfig(model_name = MODEL_NAME, temperature = 0.3),
                tracing_service
            ),
            max_context_window_size = 12,
            context_window_middleware = MiddlewareSlidingWindow(step = 2),
            max_iterations = 3
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
        max_context_window_size = 40,
        operation_pipeline = OperationPipeline(policy, tracing_service),
        tracing_service = tracing_service
    )
