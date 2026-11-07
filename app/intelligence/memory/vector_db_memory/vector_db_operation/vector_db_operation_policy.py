from abc import ABC, abstractmethod

from app.intelligence.memory import VectorDbOperation
from app.intelligence.memory import VectorDbMemoryEntry


class VectorDbOperationPolicy(ABC):
    """Decides which sequence of VectorDbOperation instances to apply for a
    given retrieval intent. Concrete subclasses encode a specific query strategy
    — pure similarity search, filtered search, search followed by reranking, or
    any combination thereof. The policy is stateless: given the same query vector,
    top_k and entry list it always produces the same operation pipeline, which the
    VectorDbOperationManager then executes.

    It receives the query as text as well as its vector. A policy that ranks by meaning
    alone ignores the text, but one that also matches words — keyword or hybrid
    search — cannot work from a vector, which has already lost them."""

    @abstractmethod
    def resolve(self, entries: list[VectorDbMemoryEntry], query: str,
        query_vector: list[float], top_k: int) -> list[VectorDbOperation]:
        raise NotImplementedError("Must be implemented")
