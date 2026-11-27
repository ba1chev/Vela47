from app.intelligence.memory import describe_entry
from app.intelligence.memory import cosine_similarity
from app.intelligence.memory import VectorDbOperation
from app.intelligence.memory import RANKING_TRACE_LIMIT
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.memory import VectorDbOperationType
from app.intelligence.tracing import current_tracing_service


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
            ((cosine_similarity(current.vector, self._query_vector), current) for current in entries),
            key = lambda current_pair: current_pair[0],
            reverse = True
        )
        current_tracing_service().record("Dense ranking", "retrieval", {
            "detail": f"{len(entries)} chunks by cosine similarity, best {scored[0][0]:.3f}" if scored else "nothing to rank",
            "entries": len(entries),
            "top_k": self._top_k,
            "ranking": [describe_entry(current, score) for score, current in scored[:RANKING_TRACE_LIMIT]]
        })
        return [current for _, current in scored[:self._top_k]]
