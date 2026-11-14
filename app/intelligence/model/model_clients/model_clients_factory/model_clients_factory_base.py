from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.model import ModelClientType
from app.intelligence.model import ModelClientBase


class ModelClientsFactoryBase(ABC):
    """Abstract factory for ModelClientBase instances. Lets the server pick the backend
    of its environment by type without importing the concrete clients."""

    @abstractmethod
    def create(self, type: ModelClientType, **kwargs: Any) -> ModelClientBase:
        raise NotImplementedError("Must be implemented")
