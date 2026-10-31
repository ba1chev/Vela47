from typing import Optional

from app.intelligence.agents.prompts.prompt_manager import PromptManager
from app.intelligence.tracing.tracing_service_base import TracingServiceBase
from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_subagent import OperationSubagent
from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_type import OperationSubagentType
from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_blueprint import OperationSubagentBlueprint
from app.intelligence.agents.deep_agent.operation_layers.operation_sanbox.operation_sandbox_env.operation_sandbox_env import OperationSandboxEnv
from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_subagents_factory.operation_subagent_factory_base import OperationSubagentFactoryBase


class OperationSubagentFactory(OperationSubagentFactoryBase):
    """Resolves a subagent type through a blueprint map into a fully configured agent,
    bound to the sandbox it was leased.

    The blueprints are supplied at construction rather than hard-coded, so which types
    a pipeline supports is a deployment decision: a pipeline given only a RESEARCH
    blueprint simply cannot run a plan that asks for CODE, and fails here with a clear
    error instead of silently substituting an agent.

    Every call builds a new agent, a new tool and a new prompt. That is required, not
    incidental — each task must start from an empty ShortTermMemory, and its tool must
    act on the sandbox this task was given rather than one a previous task held."""

    def __init__(self, blueprints: dict[OperationSubagentType, OperationSubagentBlueprint],
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        self._blueprints = dict(blueprints)
        self._tracing_service = tracing_service

    def create(self, type: OperationSubagentType,
        sandbox_env: OperationSandboxEnv) -> OperationSubagent:
        blueprint = self._blueprints.get(type)

        if blueprint is None:
            raise ValueError(
                f"No blueprint registered for subagent type '{type}'. "
                f"Known types: {list(self._blueprints)}"
            )

        tool = blueprint.tool_factory(sandbox_env)
        prompt_manager = PromptManager()
        prompt_manager.register("role", blueprint.prompt_template.format(tool = tool.name))

        return OperationSubagent(
            model = blueprint.model,
            prompt_manager = prompt_manager,
            max_context_window_size = blueprint.max_context_window_size,
            tool = tool,
            context_window_middleware = blueprint.context_window_middleware,
            max_iterations = blueprint.max_iterations,
            tracing_service = self._tracing_service
        )

    def __contains__(self, type: OperationSubagentType) -> bool:
        return type in self._blueprints
