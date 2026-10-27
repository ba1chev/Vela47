from abc import ABC, abstractmethod

from app.memory.vector_db_memory.vector_db_memory_entry import VectorDbMemoryEntry
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation import VectorDbOperation


class VectorDbOperationPolicy(ABC):
    """Decides which sequence of VectorDbOperation instances to apply for a
    given retrieval intent. Concrete subclasses encode a specific query strategy
    — pure similarity search, filtered search, search followed by reranking, or
    any combination thereof. The policy is stateless: given the same query vector,
    top_k and entry list it always produces the same operation pipeline, which the
    VectorDbOperationManager then executes."""

    @abstractmethod
    def resolve(self, entries: list[VectorDbMemoryEntry],
        query_vector: list[float], top_k: int) -> list[VectorDbOperation]:
        raise NotImplementedError("Must be implemented")
