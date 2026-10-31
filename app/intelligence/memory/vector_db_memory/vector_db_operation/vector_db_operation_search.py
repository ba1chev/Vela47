from app.intelligence.memory.vector_db_memory.vector_db_memory_entry import VectorDbMemoryEntry
from app.intelligence.memory.vector_db_memory.vector_db_operation.vector_db_utils import cosine_similarity
from app.intelligence.memory.vector_db_memory.vector_db_operation.vector_db_operation import VectorDbOperation
from app.intelligence.memory.vector_db_memory.vector_db_operation.vector_db_operation_type import VectorDbOperationType


class VectorDbOperationSearch(VectorDbOperation):
    """Ranks every entry in the store by cosine similarity to the query vector
    and returns the top_k closest matches. Cosine similarity is chosen because
    it is invariant to vector magnitude — only the direction (semantic content)
    matters, not the scale produced by different embedding models. Entries with
    a zero-norm vector score 0.0 and naturally sort to the bottom. Supply both
    parameters at construction time:
    VectorDbOperationSearch(query_vector=vec, top_k=5)."""

    def __init__(self, query_vector: list[float], top_k: int) -> None:
        self._query_vector = query_vector
        self._top_k = top_k

    @property
    def operation_type(self) -> VectorDbOperationType:
        return VectorDbOperationType.SEARCH

    def apply(self, entries: list[VectorDbMemoryEntry]) -> list[VectorDbMemoryEntry]:
        scored = sorted(
            entries,
            key = lambda e: cosine_similarity(e.vector, self._query_vector),
            reverse = True
        )
        return scored[:self._top_k]
