from typing import Any

from app.intelligence.agents.deep_agent.operation_layers.operation_layer_type import OperationType
from app.intelligence.agents.deep_agent.operation_layers.operation_layer_base import OperationLayerBase
from app.intelligence.agents.deep_agent.operation_layers.operation_layers_factory.operation_layers_registry import OPERATION_LAYERS_REGISTRY
from app.intelligence.agents.deep_agent.operation_layers.operation_layers_factory.operation_layers_factory_base import OperationLayersFactoryBase


class OperationLayersFactory(OperationLayersFactoryBase):
    """Concrete factory that maps each OperationType to its corresponding
    OperationLayerBase subclass and delegates construction to it. Additional
    keyword arguments are forwarded verbatim, so the policy can supply each
    layer's own dependencies — a model for the stages that call one, a subagent
    factory and sandbox pool for the stage that runs agents — without the
    factory needing to know about them explicitly.

    Registry reference:
      PLANNING      -> OperationPlanningLayer(model=<ModelFoundation>)
      DECOMPOSITION -> OperationDecompositionLayer()
      SUBAGENTS     -> OperationSubagentsLayer(subagent_factory=<...>, sandbox_pool=<...>)
      MERGING       -> OperationMergingLayer(model=<ModelFoundation>)"""

    def create(self, type: OperationType, **kwargs: Any) -> OperationLayerBase:
        cls = OPERATION_LAYERS_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No layer class registered for type '{type}'. "
                f"Known types: {list(OPERATION_LAYERS_REGISTRY)}"
            )

        return cls(**kwargs)
