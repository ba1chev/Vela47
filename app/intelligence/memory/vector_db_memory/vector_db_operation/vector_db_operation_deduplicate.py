from app.intelligence.memory import describe_entry
from app.intelligence.memory import cosine_similarity
from app.intelligence.memory import VectorDbOperation
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.memory import VectorDbOperationType
from app.intelligence.tracing import current_tracing_service


class VectorDbOperationDeduplicate(VectorDbOperation):
    """Removes entries whose vector is too similar to an already-accepted entry,
    preserving insertion order. Two entries are considered duplicates when their
    cosine similarity meets or exceeds `threshold`. Use this after SEARCH to
    eliminate near-identical passages that would otherwise crowd the result set
    with redundant context. Defaults to 0.95 — adjust downward to be stricter,
    upward to tolerate more repetition:
    VectorDbOperationDeduplicate(threshold=0.90)."""

    def __init__(self, threshold: float = 0.95) -> None:
        self._threshold = threshold

    @property
    def operation_type(self) -> VectorDbOperationType:
        return VectorDbOperationType.DEDUPLICATE

    def apply(self, entries: list[VectorDbMemoryEntry]) -> list[VectorDbMemoryEntry]:
        kept: list[VectorDbMemoryEntry] = []
        removed: list[dict] = []
        for entry in entries:
            similarities = [(cosine_similarity(entry.vector, current.vector), current) for current in kept]
            duplicates = [current_pair for current_pair in similarities if current_pair[0] >= self._threshold]
            if not duplicates:
                kept.append(entry)
                continue
            similarity, original = duplicates[0]
            removed.append(describe_entry(entry, similarity, duplicate_of = original.message.id))
        current_tracing_service().record("Deduplicate", "retrieval", {
            "detail": f"{len(removed)} near-duplicate(s) removed at cosine ≥ {self._threshold}, {len(kept)} kept",
            "threshold": self._threshold,
            "removed": removed
        })
        return kept
