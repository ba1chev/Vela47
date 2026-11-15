from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.memory import VectorDBSearchApproximateBase
from app.intelligence.memory import VectorDBSearchApproximateType


class VectorDBSearchApproximateFactoryBase(ABC):
    """Abstract factory that defines the contract for instantiating approximate
    nearest neighbour searches. Subclasses implement create() to map each
    VectorDBSearchApproximateType to its concrete class, so callers never name an
    index class directly."""

    @abstractmethod
    def create(self, type: VectorDBSearchApproximateType, **kwargs: Any) -> VectorDBSearchApproximateBase:
        raise NotImplementedError("Must be implemented")
