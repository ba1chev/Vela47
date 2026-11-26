from typing import Any

from app.intelligence.agents import OperationType
from app.intelligence.agents import OperationLayerBase
from app.intelligence.agents import OPERATION_LAYERS_REGISTRY
from app.intelligence.agents import OperationLayersFactoryBase


class OperationLayersFactory(OperationLayersFactoryBase):
    """Concrete factory that maps each OperationType to its OperationLayerBase subclass
    and delegates construction to it. Keyword arguments are forwarded verbatim, so the
    policy supplies each layer's own dependencies — a tracer, a model, a subagent factory
    and sandbox pool — without the factory knowing which layer takes which.

    Registry reference:
      SECURITY      -> OperationSecurityLayer(tracing_service=<TracingServiceBase>)
      PLANNING      -> OperationPlanningLayer(model=<ModelFoundation>)
      DECOMPOSITION -> OperationDecompositionLayer()
      SUBAGENTS     -> OperationSubagentsLayer(subagent_factory=<...>, sandbox_pool=<...>, peering=<...>)
      MERGING       -> OperationMergingLayer(model=<ModelFoundation>)"""

    def create(self, type: OperationType, **kwargs: Any) -> OperationLayerBase:
        cls = OPERATION_LAYERS_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No layer class registered for type '{type}'. "
                f"Known types: {list(OPERATION_LAYERS_REGISTRY)}"
            )

        return cls(**kwargs)
