from app.memory.vector_db_memory.vector_db_memory_entry import VectorDbMemoryEntry
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation import VectorDbOperation


class VectorDbOperationManager:
    """Executes an ordered pipeline of VectorDbOperation instances against a
    list of VectorDbMemoryEntry objects. Each operation receives the output of
    the previous one, forming a composable retrieval and refinement chain.
    The manager owns no state beyond the pipeline — it never reads from or
    writes to the vector store directly, and the same instance can safely
    process multiple independent pipelines."""

    def apply(self, operations: list[VectorDbOperation],
        entries: list[VectorDbMemoryEntry]) -> list[VectorDbMemoryEntry]:
        result = entries
        for operation in operations:
            result = operation.apply(result)
        return result
