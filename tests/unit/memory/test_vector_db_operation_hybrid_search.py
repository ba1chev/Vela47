from app.intelligence.messages import MessageSystem
from app.intelligence.memory import HybridSearchPolicy
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.memory import VectorDbOperationType
from app.intelligence.memory import VECTOR_DB_OPERATION_REGISTRY
from app.intelligence.memory import VectorDbOperationHybridSearch


def entry(text, vector):
    return VectorDbMemoryEntry(message = MessageSystem(content = text), vector = vector)


DEPLOY = entry("The deploy script lives in scripts/deploy.sh.", [1.0, 0.0, 0.0])
ERROR = entry("Error E1042 means the RDS secret could not be read.", [0.0, 0.2, 1.0])
COFFEE = entry("The coffee machine is on the third floor.", [0.0, 1.0, 0.0])
ENTRIES = [COFFEE, ERROR, DEPLOY]


class TestVectorDbOperationHybridSearch:
    def test_its_type_is_hybrid_search(self):
        assert VectorDbOperationHybridSearch("x", [1.0, 0.0, 0.0], 2).operation_type is VectorDbOperationType.HYBRID_SEARCH

    def test_an_entry_close_in_meaning_and_in_words_comes_first(self):
        found = VectorDbOperationHybridSearch("deploy script", [1.0, 0.0, 0.0], 3).apply(ENTRIES)
        assert found[0] is DEPLOY

    def test_an_exact_word_lifts_an_entry_that_meaning_alone_ranks_low(self):
        found = VectorDbOperationHybridSearch("E1042", [1.0, 0.0, 0.0], 2).apply(ENTRIES)
        assert ERROR in found

    def test_top_k_caps_the_result(self):
        assert len(VectorDbOperationHybridSearch("deploy", [1.0, 0.0, 0.0], 1).apply(ENTRIES)) == 1

    def test_the_new_types_are_registered(self):
        assert VectorDbOperationType.KEYWORD_SEARCH in VECTOR_DB_OPERATION_REGISTRY
        assert VectorDbOperationType.HYBRID_SEARCH in VECTOR_DB_OPERATION_REGISTRY


class TestHybridSearchPolicy:
    def test_it_searches_hybrid_then_deduplicates(self):
        operations = HybridSearchPolicy().resolve(ENTRIES, "deploy", [1.0, 0.0, 0.0], top_k = 2)
        assert [current.operation_type for current in operations] == [
            VectorDbOperationType.HYBRID_SEARCH, VectorDbOperationType.DEDUPLICATE
        ]

    def test_it_oversamples_so_deduplication_leaves_enough(self):
        operations = HybridSearchPolicy(oversample = 3).resolve(ENTRIES, "the", [1.0, 0.0, 0.0], top_k = 1)
        assert len(operations[0].apply(ENTRIES)) == 3
