import pytest

from app.intelligence.agents import RagSemanticScoringType
from app.intelligence.agents import RagSemanticScoringFactory
from tests.fixtures.model.fake_embeddings import FakeEmbeddings
from app.intelligence.agents import RagSemanticScoringTextTiling
from app.intelligence.agents import RAG_SEMANTIC_SCORING_REGISTRY

SERVERS = [
    "The cluster runs the server on one instance. ",
    "The server instance sits in the cluster subnet. ",
    "The cluster restarts the server instance on failure. ",
    "Every server instance in the cluster logs to one group. "
]
BAKING = [
    "Mix the flour with sugar and butter. ",
    "The butter and sugar melt before the flour goes in. ",
    "Bake the flour dough until the sugar browns. ",
    "Serve the butter cake once the sugar cools."
]


def make_scoring(chunk_chars = 1000, **kwargs):
    return RagSemanticScoringTextTiling(FakeEmbeddings(), chunk_chars, **kwargs)


class TestRagSemanticScoringTextTiling:
    def test_its_type_is_text_tiling(self):
        assert make_scoring().scoring_type is RagSemanticScoringType.TEXT_TILING

    def test_every_sentence_is_embedded_once_in_one_call_without_its_whitespace(self):
        scoring = make_scoring()
        scoring.score(SERVERS + BAKING)
        assert scoring._embeddings.calls == [[current.strip() for current in SERVERS + BAKING]]

    def test_there_is_a_cut_cost_for_every_gap_and_none_before_the_first_sentence(self):
        cut_costs, _ = make_scoring().score(SERVERS + BAKING)
        assert len(cut_costs) == 8 and cut_costs[0] == 0.0

    def test_cutting_costs_least_where_the_topic_changes(self):
        cut_costs, _ = make_scoring().score(SERVERS + BAKING)
        assert min(range(1, 8), key = lambda gap: cut_costs[gap]) == 4

    def test_a_paragraph_break_takes_the_discount_off_its_cut(self):
        units = SERVERS + BAKING
        broken = units[:3] + [units[3].rstrip() + "\n\n"] + units[4:]
        plain_costs, _ = make_scoring(paragraph_discount = 0.8).score(units)
        broken_costs, _ = make_scoring(paragraph_discount = 0.8).score(broken)
        assert broken_costs[4] == pytest.approx(plain_costs[4] - 0.8)
        assert broken_costs[:4] + broken_costs[5:] == pytest.approx(plain_costs[:4] + plain_costs[5:])

    def test_a_sentence_on_the_chunks_topic_is_cheaper_to_add_than_one_off_it(self):
        _, extend_costs = make_scoring().score(SERVERS + BAKING)
        assert extend_costs[(2, 3)] < extend_costs[(3, 4)]

    def test_extensions_are_priced_only_for_chunks_that_fit(self):
        units = SERVERS + BAKING
        _, extend_costs = make_scoring(chunk_chars = 120).score(units)
        assert extend_costs and all(sum(map(len, units[start:index + 1])) <= 120 for start, index in extend_costs)

    def test_costs_are_never_negative(self):
        cut_costs, extend_costs = make_scoring(cut_fee = 0.0, paragraph_discount = 5.0).score(SERVERS + BAKING)
        assert min(cut_costs) >= 0.0 and min(extend_costs.values()) >= 0.0

    def test_a_non_positive_chunk_length_is_refused(self):
        with pytest.raises(ValueError):
            make_scoring(chunk_chars = 0)

    def test_an_empty_window_is_refused(self):
        with pytest.raises(ValueError):
            make_scoring(window_sentences = 0)

    def test_a_negative_weight_is_refused(self):
        with pytest.raises(ValueError):
            make_scoring(extend_weight = -0.1)


class TestRagSemanticScoringFactory:
    def test_every_type_is_registered(self):
        assert set(RAG_SEMANTIC_SCORING_REGISTRY) == set(RagSemanticScoringType)

    def test_it_builds_each_type_with_forwarded_arguments(self):
        embeddings = FakeEmbeddings()
        scoring = RagSemanticScoringFactory().create(
            RagSemanticScoringType.TEXT_TILING, embeddings = embeddings, chunk_chars = 500, window_sentences = 2
        )
        assert scoring.scoring_type is RagSemanticScoringType.TEXT_TILING and scoring._embeddings is embeddings
        assert (scoring._chunk_chars, scoring._window_sentences) == (500, 2)

    def test_an_unknown_type_raises_value_error(self):
        with pytest.raises(ValueError):
            RagSemanticScoringFactory().create("cosine", embeddings = FakeEmbeddings(), chunk_chars = 100)
