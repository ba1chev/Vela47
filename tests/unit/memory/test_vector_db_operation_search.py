from app.messages.message_human import MessageHuman
from app.memory.vector_db_memory.vector_db_memory_entry import VectorDbMemoryEntry
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_type import VectorDbOperationType
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_search import VectorDbOperationSearch


def entry(content, vector):
    return VectorDbMemoryEntry(message = MessageHuman(content = content), vector = vector)


ENTRIES = [
    entry("Python basics", [1.0, 0.0, 0.0]),
    entry("Coffee recipes", [0.0, 1.0, 0.0]),
    entry("Python async", [0.9, 0.1, 0.0]),
    entry("Python typing", [0.85, 0.15, 0.0]),
    entry("Tea brewing", [0.0, 0.9, 0.1])
]


class TestVectorDbOperationSearch:
    def test_returns_top_k(self):
        result = VectorDbOperationSearch(query_vector = [1.0, 0.0, 0.0], top_k = 2).apply(ENTRIES)
        assert len(result) == 2

    def test_most_similar_first(self):
        result = VectorDbOperationSearch(query_vector = [1.0, 0.0, 0.0], top_k = 1).apply(ENTRIES)
        assert result[0].message.content == "Python basics"

    def test_top_k_larger_than_list(self):
        result = VectorDbOperationSearch(query_vector = [1.0, 0.0, 0.0], top_k = 100).apply(ENTRIES)
        assert len(result) == len(ENTRIES)

    def test_empty_entries(self):
        result = VectorDbOperationSearch(query_vector = [1.0, 0.0], top_k = 3).apply([])
        assert result == []

    def test_operation_type(self):
        op = VectorDbOperationSearch(query_vector = [1.0], top_k = 1)
        assert op.operation_type == VectorDbOperationType.SEARCH
