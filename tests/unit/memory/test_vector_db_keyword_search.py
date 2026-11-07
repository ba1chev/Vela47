from app.intelligence.memory import tokenize
from app.intelligence.messages import MessageSystem
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.memory import VectorDbKeywordIndex
from app.intelligence.memory import VectorDbOperationType
from app.intelligence.memory import reciprocal_rank_fusion
from app.intelligence.memory import VectorDbOperationKeywordSearch


def entry(text, vector = None):
    return VectorDbMemoryEntry(message = MessageSystem(content = text), vector = vector or [1.0, 0.0])


ENTRIES = [
    entry("The deploy script needs AWS_PROFILE set."),
    entry("Error E1042 means the RDS secret could not be read."),
    entry("Грешка E1042 означава, че тайната не може да бъде прочетена."),
    entry("The coffee machine is cleaned on Fridays.")
]


class TestTokenize:
    def test_words_are_lower_cased(self):
        assert tokenize("Deploy SCRIPT") == ["deploy", "script"]

    def test_cyrillic_words_are_words_too(self):
        assert tokenize("Грешка E1042") == ["грешка", "e1042"]

    def test_punctuation_separates_words(self):
        assert tokenize("a.b,c") == ["a", "b", "c"]


class TestVectorDbKeywordIndex:
    def test_an_entry_without_the_word_scores_zero(self):
        scores = VectorDbKeywordIndex(ENTRIES).scores("E1042")
        assert scores[0] == 0.0 and scores[3] == 0.0

    def test_entries_with_the_word_score_above_zero(self):
        scores = VectorDbKeywordIndex(ENTRIES).scores("E1042")
        assert scores[1] > 0.0 and scores[2] > 0.0

    def test_a_rare_word_outweighs_a_common_one(self):
        entries = [entry("alpha common"), entry("beta common"), entry("gamma common")]
        scores = VectorDbKeywordIndex(entries).scores("alpha common")
        assert scores[0] > scores[1]

    def test_a_shorter_passage_wins_on_equal_counts(self):
        entries = [entry("token"), entry("token " + "filler " * 30)]
        scores = VectorDbKeywordIndex(entries).scores("token")
        assert scores[0] > scores[1]

    def test_an_empty_list_scores_nothing(self):
        assert VectorDbKeywordIndex([]).scores("anything") == []


class TestVectorDbOperationKeywordSearch:
    def test_its_type_is_keyword_search(self):
        assert VectorDbOperationKeywordSearch("x", 3).operation_type is VectorDbOperationType.KEYWORD_SEARCH

    def test_only_entries_sharing_a_word_are_returned(self):
        found = VectorDbOperationKeywordSearch("E1042", 10).apply(ENTRIES)
        assert {current.message.content for current in found} == {ENTRIES[1].message.content, ENTRIES[2].message.content}

    def test_top_k_caps_the_result(self):
        assert len(VectorDbOperationKeywordSearch("e1042", 1).apply(ENTRIES)) == 1

    def test_no_match_returns_nothing(self):
        assert VectorDbOperationKeywordSearch("kubernetes", 5).apply(ENTRIES) == []


class TestReciprocalRankFusion:
    def test_agreement_beats_a_single_first_place(self):
        a, b, c = object(), object(), object()
        fused = reciprocal_rank_fusion([[a, b, c], [b, c, a]])
        assert fused[0] is b

    def test_an_item_in_only_one_ranking_is_kept(self):
        a, b = object(), object()
        assert b in reciprocal_rank_fusion([[a], [b]])

    def test_each_item_appears_once(self):
        a, b = object(), object()
        assert len(reciprocal_rank_fusion([[a, b], [a, b]])) == 2
