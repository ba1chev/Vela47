from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.memory import VectorDBSearchUninformedBase
from app.intelligence.memory import VectorDBSearchUninformedType


class VectorDBSearchUninformedFactoryBase(ABC):
    """Abstract factory that defines the contract for instantiating uninformed
    searches. Subclasses implement create() to map each VectorDBSearchUninformedType
    to its concrete class, so callers never name an algorithm class directly."""

    @abstractmethod
    def create(self, type: VectorDBSearchUninformedType, **kwargs: Any) -> VectorDBSearchUninformedBase:
        raise NotImplementedError("Must be implemented")
