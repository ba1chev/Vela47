from typing import Optional

from app.intelligence.tools import ToolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.agents import PromptManager
from app.intelligence.tools import ToolMessageWorker
from app.intelligence.agents import OperationSubagent
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.agents import SUBAGENT_PEER_PROMPT
from app.intelligence.agents import OperationSubagentType
from app.intelligence.agents import OperationSubagentBlueprint
from app.intelligence.agents import OperationSubagentFactoryBase


class OperationSubagentFactory(OperationSubagentFactoryBase):
    """Resolves a subagent type through a blueprint map into a fully configured agent,
    bound to the sandbox it was leased.

    The blueprints are supplied at construction rather than hard-coded, so which types
    a pipeline supports is a deployment decision: a pipeline given only a RESEARCH
    blueprint simply cannot run a plan that asks for CODE, and fails here with a clear
    error instead of silently substituting an agent.

    Every call builds a new agent, new tools and a new prompt. That is required, not
    incidental — each task must start from an empty ShortTermMemory, and its tools must
    act on the sandbox this task was given rather than one a previous task held. A
    peer_tool joins the toolset, and SUBAGENT_PEER_PROMPT tells the model when to use it."""

    def __init__(self, blueprints: dict[OperationSubagentType, OperationSubagentBlueprint],
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        self._blueprints = dict(blueprints)
        self._tracing_service = tracing_service

    def _prompt(self, blueprint: OperationSubagentBlueprint, tools: list[ToolBase],
        peer_tool: Optional[ToolMessageWorker]) -> str:
        prompt = blueprint.prompt_template.format(tools = ", ".join(current_tool.name for current_tool in tools))
        if peer_tool is None:
            return prompt
        return prompt + SUBAGENT_PEER_PROMPT.format(
            peer = peer_tool.peer_name,
            max_messages = peer_tool.max_messages
        )

    def create(self, type: OperationSubagentType, sandbox_env: SandboxEnv,
        peer_tool: Optional[ToolMessageWorker] = None) -> OperationSubagent:
        blueprint = self._blueprints.get(type)

        if blueprint is None:
            raise ValueError(
                f"No blueprint registered for subagent type '{type}'. "
                f"Known types: {list(self._blueprints)}"
            )

        tools = [current_factory(sandbox_env) for current_factory in blueprint.tool_factories]
        if peer_tool is not None:
            tools.append(peer_tool)
        prompt_manager = PromptManager()
        prompt_manager.register("role", self._prompt(blueprint, tools, peer_tool))

        return OperationSubagent(
            model = blueprint.model,
            prompt_manager = prompt_manager,
            max_context_window_size = blueprint.max_context_window_size,
            tools = tools,
            context_window_middleware = blueprint.context_window_middleware,
            max_iterations = blueprint.max_iterations,
            tracing_service = self._tracing_service,
            probes = [current_factory(sandbox_env) for current_factory in blueprint.probe_factories]
        )

    def __contains__(self, type: OperationSubagentType) -> bool:
        return type in self._blueprints
