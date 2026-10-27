from app.messages.message_human import MessageHuman
from app.memory.vector_db_memory.vector_db_memory_entry import VectorDbMemoryEntry
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_type import VectorDbOperationType
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_policy_semantic_search import SemanticSearchPolicy


def entry(content, vector):
    return VectorDbMemoryEntry(message = MessageHuman(content = content), vector = vector)


ENTRIES = [
    entry("Python basics",  [1.0, 0.0, 0.0]),
    entry("Coffee recipes", [0.0, 1.0, 0.0]),
    entry("Python async",   [0.9, 0.1, 0.0]),
    entry("Python typing",  [0.85, 0.15, 0.0]),
    entry("Tea brewing",    [0.0, 0.9, 0.1]),
]


class TestSemanticSearchPolicy:
    def test_returns_single_search_operation(self):
        ops = SemanticSearchPolicy().resolve(ENTRIES, [1.0, 0.0, 0.0], top_k = 3)
        assert len(ops) == 1
        assert ops[0].operation_type == VectorDbOperationType.SEARCH

    def test_result_count_matches_top_k(self):
        ops = SemanticSearchPolicy().resolve(ENTRIES, [1.0, 0.0, 0.0], top_k = 2)
        result = ops[0].apply(ENTRIES)
        assert len(result) == 2
