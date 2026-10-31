from typing import Callable

from app.intelligence.memory.vector_db_memory.vector_db_memory_entry import VectorDbMemoryEntry
from app.intelligence.memory.vector_db_memory.vector_db_operation.vector_db_operation import VectorDbOperation
from app.intelligence.memory.vector_db_memory.vector_db_operation.vector_db_operation_type import VectorDbOperationType


class VectorDbOperationFilter(VectorDbOperation):
    """Retains only the entries for which a caller-supplied predicate returns
    True, discarding all others. Use this to apply metadata or role constraints
    before or after SEARCH — for example, keeping only human messages, entries
    from a specific time window, or entries whose content exceeds a minimum
    length. The predicate is a pure function that receives a VectorDbMemoryEntry
    and returns bool: VectorDbOperationFilter(predicate=lambda e: ...)."""

    def __init__(self, predicate: Callable[[VectorDbMemoryEntry], bool]) -> None:
        self._predicate = predicate

    @property
    def operation_type(self) -> VectorDbOperationType:
        return VectorDbOperationType.FILTER

    def apply(self, entries: list[VectorDbMemoryEntry]) -> list[VectorDbMemoryEntry]:
        return [e for e in entries if self._predicate(e)]
