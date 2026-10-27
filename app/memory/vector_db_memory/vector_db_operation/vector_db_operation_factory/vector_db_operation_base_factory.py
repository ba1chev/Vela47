from typing import Any
from abc import ABC, abstractmethod

from app.memory.vector_db_memory.vector_db_operation.vector_db_operation import VectorDbOperation
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_type import VectorDbOperationType


class VectorDbOperationBaseFactory(ABC):
    """Abstract factory that defines the contract for instantiating
    VectorDbOperation objects. Subclasses implement create() to map each
    VectorDbOperationType to its concrete class, keeping the operation
    pipeline decoupled from individual operation implementations."""

    @abstractmethod
    def create(self, type: VectorDbOperationType, **kwargs: Any) -> VectorDbOperation:
        raise NotImplementedError("Must be implemented")
