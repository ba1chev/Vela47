from abc import ABC, abstractmethod

from app.intelligence.agents.deep_agent.operation_layers.operation_layer_base import OperationLayerBase
from app.intelligence.agents.deep_agent.operation_layers.operation_layers_factory.operation_layers_factory_base import OperationLayersFactoryBase


class OperationPolicy(ABC):
    """Decides which layers an OperationPipeline runs and in what order, and
    supplies each one its dependencies. Mirrors ContextWindowPolicy: the policy
    resolves a concrete, ready-to-run sequence, and the thing that executes it
    stays ignorant of how that sequence was chosen.

    The factory is passed in rather than held, so a policy never imports a
    concrete layer class — it names types and lets the factory construct them.
    That is also why dependencies live on the policy: it is the only component
    that knows both which layers will run and what each of them needs."""

    @abstractmethod
    def resolve(self, factory: OperationLayersFactoryBase) -> list[OperationLayerBase]:
        raise NotImplementedError("Must be implemented")
