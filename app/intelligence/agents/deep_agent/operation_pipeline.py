from app.intelligence.agents.deep_agent.operation_context import OperationContext
from app.intelligence.agents.deep_agent.operation_policies.operation_policy import OperationPolicy
from app.intelligence.agents.deep_agent.operation_layers.operation_layer_base import OperationLayerBase
from app.intelligence.agents.deep_agent.operation_layers.operation_layers_factory.operation_layers_factory import OperationLayersFactory
from app.intelligence.agents.deep_agent.operation_layers.operation_layers_factory.operation_layers_factory_base import OperationLayersFactoryBase


class OperationPipeline:
    """Executes the layer sequence an OperationPolicy resolved, threading one
    OperationContext through all of them.

    The pipeline is intentionally the dumbest component here: it holds no
    knowledge of what any layer does, does not branch, and does not inspect the
    context between stages. Everything variable — which stages run, in what
    order, with which dependencies — is decided by the policy at construction
    time. Adding a stage therefore never touches this class.

    Layers are resolved once in the constructor rather than per run, so a
    pipeline is a reusable, immutable plan of execution."""

    def __init__(self, operation_policy: OperationPolicy) -> None:
        self._operation_policy: OperationPolicy = operation_policy
        operation_layers_factory: OperationLayersFactoryBase = OperationLayersFactory()
        self._operation_layers: list[OperationLayerBase] = operation_policy.resolve(
            operation_layers_factory
        )

    def run(self, context: OperationContext) -> OperationContext:
        for current_layer in self._operation_layers:
            current_layer.execute(context)
        return context

    def __len__(self) -> int:
        return len(self._operation_layers)
