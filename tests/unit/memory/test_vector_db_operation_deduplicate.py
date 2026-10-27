from app.messages.message_human import MessageHuman
from app.memory.vector_db_memory.vector_db_memory_entry import VectorDbMemoryEntry
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_type import VectorDbOperationType
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_deduplicate import VectorDbOperationDeduplicate


def entry(content, vector):
    return VectorDbMemoryEntry(message = MessageHuman(content = content), vector = vector)


ENTRIES = [
    entry("Python basics", [1.0, 0.0, 0.0]),
    entry("Coffee recipes", [0.0, 1.0, 0.0]),
    entry("Python async", [0.9, 0.1, 0.0]),
    entry("Python typing", [0.85, 0.15, 0.0]),
    entry("Tea brewing", [0.0, 0.9, 0.1])
]


class TestVectorDbOperationDeduplicate:
    def test_removes_near_duplicates(self):
        dupes = [
            entry("A", [1.0, 0.0]),
            entry("A copy", [0.999, 0.001]),
            entry("B", [0.0, 1.0])
        ]
        result = VectorDbOperationDeduplicate(threshold = 0.99).apply(dupes)
        assert len(result) == 2

    def test_keeps_all_when_diverse(self):
        result = VectorDbOperationDeduplicate(threshold = 0.999).apply(ENTRIES)
        assert len(result) == len(ENTRIES)

    def test_preserves_insertion_order(self):
        result = VectorDbOperationDeduplicate(threshold = 0.5).apply(ENTRIES)
        assert result[0].message.content == ENTRIES[0].message.content

    def test_empty_list(self):
        assert VectorDbOperationDeduplicate().apply([]) == []

    def test_operation_type(self):
        assert VectorDbOperationDeduplicate().operation_type == VectorDbOperationType.DEDUPLICATE
