from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.agents import RagLayerBase
from app.intelligence.agents import RagLayerType


class RagLayersFactoryBase(ABC):
    """Abstract factory for RagLayerBase instances. Exists so a RagPolicy can request
    layers by type without importing the concrete layer classes, which keeps the set of
    stages swappable — a test policy can be handed a factory that returns stubs."""

    @abstractmethod
    def create(self, type: RagLayerType, **kwargs: Any) -> RagLayerBase:
        raise NotImplementedError("Must be implemented")
