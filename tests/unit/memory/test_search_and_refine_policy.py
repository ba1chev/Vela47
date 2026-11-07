from app.intelligence.messages import MessageHuman
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.memory import VectorDbOperationType
from app.intelligence.memory import SearchAndRefinePolicy


def entry(content, vector):
    return VectorDbMemoryEntry(message = MessageHuman(content = content), vector = vector)


ENTRIES = [
    entry("Python basics", [1.0, 0.0, 0.0]),
    entry("Coffee recipes", [0.0, 1.0, 0.0]),
    entry("Python async", [0.9, 0.1, 0.0]),
    entry("Python typing", [0.85, 0.15, 0.0]),
    entry("Tea brewing", [0.0, 0.9, 0.1])
]


class TestSearchAndRefinePolicy:
    def test_returns_two_operations(self):
        ops = SearchAndRefinePolicy().resolve(ENTRIES, "python", [1.0, 0.0, 0.0], top_k = 2)
        assert len(ops) == 2
        assert ops[0].operation_type == VectorDbOperationType.SEARCH
        assert ops[1].operation_type == VectorDbOperationType.DEDUPLICATE

    def test_oversamples_before_dedup(self):
        ops = SearchAndRefinePolicy(oversample = 3).resolve(ENTRIES, "python", [1.0, 0.0, 0.0], top_k = 1)
        search_op = ops[0]
        assert search_op._top_k == 3

    def test_end_to_end_diverse_results(self):
        ops = SearchAndRefinePolicy(dedup_threshold = 0.99, oversample = 2).resolve(
            ENTRIES, "python", [1.0, 0.0, 0.0], top_k = 2
        )
        result = ENTRIES
        for op in ops:
            result = op.apply(result)
        contents = [e.message.content for e in result]
        assert len(set(contents)) == len(contents)
