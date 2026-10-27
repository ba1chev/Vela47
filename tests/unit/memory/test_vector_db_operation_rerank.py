from app.messages.message_human import MessageHuman
from app.memory.vector_db_memory.vector_db_memory_entry import VectorDbMemoryEntry
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_type import VectorDbOperationType
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_rerank import VectorDbOperationRerank


def entry(content, vector):
    return VectorDbMemoryEntry(message = MessageHuman(content = content), vector = vector)


ENTRIES = [
    entry("Python basics", [1.0, 0.0, 0.0]),
    entry("Coffee recipes", [0.0, 1.0, 0.0]),
    entry("Python async", [0.9, 0.1, 0.0]),
    entry("Python typing", [0.85, 0.15, 0.0]),
    entry("Tea brewing", [0.0, 0.9, 0.1])
]


class TestVectorDbOperationRerank:
    def test_sorted_by_score_descending(self):
        result = VectorDbOperationRerank(
            scorer = lambda e: len(e.message.content)
        ).apply(ENTRIES)
        lengths = [len(e.message.content) for e in result]
        assert lengths == sorted(lengths, reverse = True)

    def test_empty_list(self):
        assert VectorDbOperationRerank(scorer = lambda e: 0).apply([]) == []

    def test_operation_type(self):
        assert VectorDbOperationRerank(scorer = lambda e: 0).operation_type == VectorDbOperationType.RERANK
