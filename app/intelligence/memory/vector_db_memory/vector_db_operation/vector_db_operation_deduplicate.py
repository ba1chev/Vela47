from app.intelligence.memory.vector_db_memory.vector_db_memory_entry import VectorDbMemoryEntry
from app.intelligence.memory.vector_db_memory.vector_db_operation.vector_db_utils import cosine_similarity
from app.intelligence.memory.vector_db_memory.vector_db_operation.vector_db_operation import VectorDbOperation
from app.intelligence.memory.vector_db_memory.vector_db_operation.vector_db_operation_type import VectorDbOperationType


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
        for entry in entries:
            is_duplicate = any(
                cosine_similarity(entry.vector, k.vector) >= self._threshold
                for k in kept
            )
            if not is_duplicate:
                kept.append(entry)
        return kept
