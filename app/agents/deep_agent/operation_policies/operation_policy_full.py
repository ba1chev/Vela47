from app.model.model_foundation.model_foundation import ModelFoundation
from app.agents.deep_agent.operation_policies.operation_policy import OperationPolicy
from app.agents.deep_agent.operation_layers.operation_layer_type import OperationType
from app.agents.deep_agent.operation_layers.operation_layer_base import OperationLayerBase
from app.agents.deep_agent.operation_layers.operation_sanbox.operation_sandbox_pool_base import OperationSandboxPoolBase
from app.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_factory_base import OperationSubagentFactoryBase
from app.agents.deep_agent.operation_layers.operation_layers_factory.operation_layers_factory_base import OperationLayersFactoryBase


class OperationPolicyFull(OperationPolicy):
    """Runs the complete pipeline — plan, decompose, execute, merge.

    The planning and merging models are separate parameters because the two jobs
    reward opposite settings: planning wants low temperature and reasoning mode
    to produce a schema-valid breakdown, merging wants a model good at prose.
    Passing the same instance twice is fine when that distinction does not
    matter."""

    def __init__(self, planning_model: ModelFoundation, merging_model: ModelFoundation,
        subagent_factory: OperationSubagentFactoryBase,
        sandbox_pool: OperationSandboxPoolBase) -> None:
        self._planning_model: ModelFoundation = planning_model
        self._merging_model: ModelFoundation = merging_model
        self._subagent_factory: OperationSubagentFactoryBase = subagent_factory
        self._sandbox_pool: OperationSandboxPoolBase = sandbox_pool

    def resolve(self, factory: OperationLayersFactoryBase) -> list[OperationLayerBase]:
        return [
            factory.create(OperationType.PLANNING, model = self._planning_model),
            factory.create(OperationType.DECOMPOSITION),
            factory.create(
                OperationType.SUBAGENTS,
                subagent_factory = self._subagent_factory,
                sandbox_pool = self._sandbox_pool
            ),
            factory.create(OperationType.MERGING, model = self._merging_model)
        ]
