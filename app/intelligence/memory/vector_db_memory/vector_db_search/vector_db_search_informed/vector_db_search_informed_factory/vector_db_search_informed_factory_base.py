from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.memory import VectorDBSearchInformedBase
from app.intelligence.memory import VectorDBSearchInformedType


class VectorDBSearchInformedFactoryBase(ABC):
    """Abstract factory that defines the contract for instantiating informed
    searches. Subclasses implement create() to map each VectorDBSearchInformedType
    to its concrete class, so callers never name an algorithm class directly."""

    @abstractmethod
    def create(self, type: VectorDBSearchInformedType, **kwargs: Any) -> VectorDBSearchInformedBase:
        raise NotImplementedError("Must be implemented")
