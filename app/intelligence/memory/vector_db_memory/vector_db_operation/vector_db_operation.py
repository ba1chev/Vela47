from abc import ABC, abstractmethod

from app.intelligence.memory.vector_db_memory.vector_db_memory_entry import VectorDbMemoryEntry
from app.intelligence.memory.vector_db_memory.vector_db_operation.vector_db_operation_type import VectorDbOperationType


class VectorDbOperation(ABC):
    """Abstract base for every transformation that can be applied to a list of
    VectorDbMemoryEntry objects. Each concrete subclass implements one operation
    type — search, filter, rerank, or deduplicate — and encapsulates its
    parameters at construction time (e.g. query vector and top_k for SEARCH).
    apply() is a pure function: it receives the full entry list and returns a
    refined one, never writing to the store directly."""

    @property
    @abstractmethod
    def operation_type(self) -> VectorDbOperationType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def apply(self, entries: list[VectorDbMemoryEntry]) -> list[VectorDbMemoryEntry]:
        raise NotImplementedError("Must be implemented")
