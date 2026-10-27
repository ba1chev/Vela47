from app.memory.vector_db_memory.vector_db_memory_entry import VectorDbMemoryEntry
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation import VectorDbOperation
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_policy import VectorDbOperationPolicy
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_search import VectorDbOperationSearch


class SemanticSearchPolicy(VectorDbOperationPolicy):
    """Returns the top_k entries most similar to the query vector using cosine
    similarity, with no further filtering or reranking. The simplest retrieval
    baseline — use this when the vector store is clean and result diversity is
    not a concern. The top_k value is supplied by the caller at search time via
    VectorDbMemory.search(), so no configuration is needed at construction."""

    def resolve(self, entries: list[VectorDbMemoryEntry],
        query_vector: list[float], top_k: int) -> list[VectorDbOperation]:
        return [VectorDbOperationSearch(query_vector = query_vector, top_k = top_k)]
