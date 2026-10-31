from typing import Any
from abc import ABC, abstractmethod

from app.agents.deep_agent.operation_layers.operation_layer_type import OperationType
from app.agents.deep_agent.operation_layers.operation_layer_base import OperationLayerBase


class OperationLayersFactoryBase(ABC):
    """Abstract factory for OperationLayerBase instances. Exists so an
    OperationPolicy can request layers by type without importing the concrete
    layer classes, which keeps the set of available stages swappable — a test
    policy can be handed a factory that returns stubs."""

    @abstractmethod
    def create(self, type: OperationType, **kwargs: Any) -> OperationLayerBase:
        raise NotImplementedError("Must be implemented")
