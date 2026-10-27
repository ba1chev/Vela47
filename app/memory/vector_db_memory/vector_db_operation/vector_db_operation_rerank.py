from typing import Callable

from app.memory.vector_db_memory.vector_db_memory_entry import VectorDbMemoryEntry
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation import VectorDbOperation
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_type import VectorDbOperationType


class VectorDbOperationRerank(VectorDbOperation):
    """Re-orders a list of entries by a caller-supplied scoring function,
    highest score first. Use this after SEARCH to apply a secondary relevance
    signal that the initial similarity ranking does not capture — for example,
    recency weighting, keyword overlap with the original query, or a cross-
    encoder score produced by a second model. The scorer is a pure function
    that receives a VectorDbMemoryEntry and returns a float:
    VectorDbOperationRerank(scorer=lambda e: ...)."""

    def __init__(self, scorer: Callable[[VectorDbMemoryEntry], float]) -> None:
        self._scorer = scorer

    @property
    def operation_type(self) -> VectorDbOperationType:
        return VectorDbOperationType.RERANK

    def apply(self, entries: list[VectorDbMemoryEntry]) -> list[VectorDbMemoryEntry]:
        return sorted(entries, key = self._scorer, reverse = True)
