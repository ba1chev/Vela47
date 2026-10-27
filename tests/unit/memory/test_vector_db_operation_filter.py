from app.messages.message_human import MessageHuman
from app.memory.vector_db_memory.vector_db_memory_entry import VectorDbMemoryEntry
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_type import VectorDbOperationType
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_filter import VectorDbOperationFilter


def entry(content, vector):
    return VectorDbMemoryEntry(message = MessageHuman(content = content), vector = vector)


ENTRIES = [
    entry("Python basics", [1.0, 0.0, 0.0]),
    entry("Coffee recipes", [0.0, 1.0, 0.0]),
    entry("Python async", [0.9, 0.1, 0.0]),
    entry("Python typing", [0.85, 0.15, 0.0]),
    entry("Tea brewing", [0.0, 0.9, 0.1])
]


class TestVectorDbOperationFilter:
    def test_keeps_matching_entries(self):
        result = VectorDbOperationFilter(
            predicate = lambda e: "Python" in e.message.content
        ).apply(ENTRIES)
        assert all("Python" in e.message.content for e in result)
        assert len(result) == 3

    def test_exclude_all(self):
        result = VectorDbOperationFilter(predicate = lambda e: False).apply(ENTRIES)
        assert result == []

    def test_include_all(self):
        result = VectorDbOperationFilter(predicate = lambda e: True).apply(ENTRIES)
        assert len(result) == len(ENTRIES)

    def test_operation_type(self):
        op = VectorDbOperationFilter(predicate = lambda e: True)
        assert op.operation_type == VectorDbOperationType.FILTER
