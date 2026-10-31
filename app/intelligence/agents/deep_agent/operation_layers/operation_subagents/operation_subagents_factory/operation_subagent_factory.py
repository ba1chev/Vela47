from typing import Optional

from app.intelligence.tracing.tracing_service_base import TracingServiceBase
from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_subagent import OperationSubagent
from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_type import OperationSubagentType
from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_blueprint import OperationSubagentBlueprint
from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_subagents_factory.operation_subagent_factory_base import OperationSubagentFactoryBase


class OperationSubagentFactory(OperationSubagentFactoryBase):
    """Concrete factory that resolves an OperationSubagentType through a
    blueprint map into a fully configured OperationSubagent. The blueprints are
    supplied at construction time rather than hard-coded, so which types a
    pipeline supports is a deployment decision: a pipeline given only a RESEARCH
    blueprint simply cannot run a plan that asks for CODE, and fails at creation
    with a clear error instead of silently substituting an agent.

    Every call constructs a new agent. That is required, not incidental — each
    task must start from an empty ShortTermMemory, so reusing one instance across
    tasks would leak one task's conversation into the next."""

    def __init__(self, blueprints: dict[OperationSubagentType, OperationSubagentBlueprint],
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        self._blueprints = dict(blueprints)
        self._tracing_service = tracing_service

    def create(self, type: OperationSubagentType) -> OperationSubagent:
        blueprint = self._blueprints.get(type)

        if blueprint is None:
            raise ValueError(
                f"No blueprint registered for subagent type '{type}'. "
                f"Known types: {list(self._blueprints)}"
            )

        return OperationSubagent(
            model = blueprint.model,
            prompt_manager = blueprint.prompt_manager,
            max_context_window_size = blueprint.max_context_window_size,
            tool = blueprint.tool,
            context_window_middleware = blueprint.context_window_middleware,
            max_iterations = blueprint.max_iterations,
            tracing_service = self._tracing_service
        )

    def __contains__(self, type: OperationSubagentType) -> bool:
        return type in self._blueprints
