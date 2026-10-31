from app.intelligence.memory import VectorDbOperation
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.memory import VectorDbOperationPolicy
from app.intelligence.memory import VectorDbOperationSearch
from app.intelligence.memory import VectorDbOperationDeduplicate


class SearchAndRefinePolicy(VectorDbOperationPolicy):
    """Retrieves a wider candidate pool via cosine similarity search, then removes
    near-duplicate entries so the final result set is diverse. Concretely:
    SEARCH(top_k * oversample) → DEDUPLICATE(threshold). The oversampling step
    ensures that after deduplication enough distinct results remain; the threshold
    controls how aggressively near-duplicates are collapsed. Use this over
    SemanticSearchPolicy when the vector store contains paraphrased or repetitive
    entries that would otherwise crowd the top results with redundant context.

    Defaults: oversample=2 (search twice as many candidates), threshold=0.95."""

    def __init__(self, dedup_threshold: float = 0.95, oversample: int = 2) -> None:
        self._dedup_threshold = dedup_threshold
        self._oversample = oversample

    def resolve(self, entries: list[VectorDbMemoryEntry],
        query_vector: list[float], top_k: int) -> list[VectorDbOperation]:
        return [
            VectorDbOperationSearch(query_vector = query_vector, top_k = top_k * self._oversample),
            VectorDbOperationDeduplicate(threshold = self._dedup_threshold),
        ]
