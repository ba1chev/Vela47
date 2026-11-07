from app.intelligence.memory import VectorDbOperation
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.memory import VectorDbOperationPolicy
from app.intelligence.memory import VectorDbOperationDeduplicate
from app.intelligence.memory import VectorDbOperationHybridSearch


class HybridSearchPolicy(VectorDbOperationPolicy):
    """Retrieves by meaning and by words together, then removes near-duplicates:
    HYBRID_SEARCH(top_k * oversample) → DEDUPLICATE(threshold). The retrieval policy of
    choice for documents, where a question may hinge on an exact term — a name, a code,
    a number — that dense search alone would rank too low, and where overlapping chunks
    of the same document would otherwise fill the results with the same sentence twice.

    Like SearchAndRefinePolicy it oversamples so that enough distinct entries survive
    deduplication, and leaves cutting the list to the caller, which knows how many
    candidates the next stage wants.

    Defaults: oversample=2, threshold=0.95."""

    def __init__(self, dedup_threshold: float = 0.95, oversample: int = 2) -> None:
        self._dedup_threshold = dedup_threshold
        self._oversample = oversample

    def resolve(self, entries: list[VectorDbMemoryEntry], query: str,
        query_vector: list[float], top_k: int) -> list[VectorDbOperation]:
        return [
            VectorDbOperationHybridSearch(
                query = query, query_vector = query_vector, top_k = top_k * self._oversample
            ),
            VectorDbOperationDeduplicate(threshold = self._dedup_threshold)
        ]
