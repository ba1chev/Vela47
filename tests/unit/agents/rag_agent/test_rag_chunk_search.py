import random
import pytest
import itertools

from app.intelligence.agents import RagChunkSearchType
from app.intelligence.agents import RagChunkSearchAStar
from app.intelligence.agents import RagChunkSearchFactory
from app.intelligence.agents import RAG_CHUNK_SEARCH_REGISTRY


def path_cost(starts, count, cut_costs, extend_costs):
    total = 0.0
    for start, end in zip(starts, starts[1:] + [count]):
        total += (cut_costs[start] if start else 0.0) + sum(extend_costs[(start, index)] for index in range(start + 1, end))
    return total


def allowed(starts, lengths, chunk_chars, min_chars):
    remaining = [sum(lengths[index:]) for index in range(len(lengths) + 1)]
    for start, end in zip(starts, starts[1:] + [len(lengths)]):
        chars = sum(lengths[start:end])
        if chars > chunk_chars:
            return False
        if end < len(lengths):
            forced = chars + lengths[end] > chunk_chars
            if not forced and (chars < min_chars or remaining[end] < min_chars):
                return False
    return True


def flat_extend_costs(lengths, chunk_chars, cost):
    return {
        (start, index): cost
        for start in range(len(lengths)) for index in range(start + 1, len(lengths))
        if sum(lengths[start:index + 1]) <= chunk_chars
    }


class TestRagChunkSearchAStar:
    def test_its_type_is_a_star(self):
        assert RagChunkSearchAStar(chunk_chars = 100, min_chars = 0).search_type is RagChunkSearchType.A_STAR

    def test_no_sentence_is_no_chunk(self):
        assert RagChunkSearchAStar(chunk_chars = 100, min_chars = 0).search([], [], {}) == []

    def test_one_sentence_is_one_chunk(self):
        assert RagChunkSearchAStar(chunk_chars = 100, min_chars = 0).search([40], [0.0], {}) == [0]

    def test_free_extensions_cut_only_where_a_chunk_is_full(self):
        lengths = [40] * 6
        starts = RagChunkSearchAStar(chunk_chars = 100, min_chars = 0).search(
            lengths, [0.0] + [1.0] * 5, flat_extend_costs(lengths, 100, 0.0)
        )
        assert starts == [0, 2, 4]

    def test_free_cuts_still_keep_chunks_above_the_shortest_length(self):
        lengths = [30] * 6
        starts = RagChunkSearchAStar(chunk_chars = 100, min_chars = 60).search(
            lengths, [0.0] * 6, flat_extend_costs(lengths, 100, 1.0)
        )
        assert allowed(starts, lengths, 100, 60) and starts == [0, 2, 4]

    def test_the_cheapest_cut_is_where_cutting_costs_least(self):
        lengths = [30] * 4
        starts = RagChunkSearchAStar(chunk_chars = 100, min_chars = 0).search(
            lengths, [0.0, 1.0, 0.1, 1.0], flat_extend_costs(lengths, 100, 0.5)
        )
        assert starts == [0, 2]

    def test_it_finds_the_cheapest_allowed_cut(self):
        search = RagChunkSearchAStar(chunk_chars = 150, min_chars = 40)
        generator = random.Random(7)
        for _ in range(40):
            lengths = [generator.randint(15, 80) for _ in range(9)]
            cut_costs = [0.0] + [generator.uniform(0.0, 2.0) for _ in range(8)]
            extend_costs = {
                (start, index): generator.uniform(0.0, 1.0)
                for start in range(9) for index in range(start + 1, 9)
                if sum(lengths[start:index + 1]) <= 150
            }
            found = search.search(lengths, cut_costs, extend_costs)
            candidates = [
                [0, *middle] for size in range(9) for middle in itertools.combinations(range(1, 9), size)
                if allowed([0, *middle], lengths, 150, 40)
            ]
            cheapest = min(path_cost(current, 9, cut_costs, extend_costs) for current in candidates)
            assert allowed(found, lengths, 150, 40) and path_cost(found, 9, cut_costs, extend_costs) == pytest.approx(cheapest)

    def test_a_non_positive_chunk_length_is_refused(self):
        with pytest.raises(ValueError):
            RagChunkSearchAStar(chunk_chars = 0, min_chars = 0)

    def test_a_shortest_chunk_longer_than_the_longest_is_refused(self):
        with pytest.raises(ValueError):
            RagChunkSearchAStar(chunk_chars = 100, min_chars = 101)


class TestRagChunkSearchFactory:
    def test_every_type_is_registered(self):
        assert set(RAG_CHUNK_SEARCH_REGISTRY) == set(RagChunkSearchType)

    def test_it_builds_each_type_with_forwarded_arguments(self):
        search = RagChunkSearchFactory().create(RagChunkSearchType.A_STAR, chunk_chars = 100, min_chars = 0)
        assert search.search_type is RagChunkSearchType.A_STAR and search.search([40] * 3, [0.0, 2.0, 1.0],{(0, 1): 0.0, (1, 2): 0.0}) == [0, 2]

    def test_an_unknown_type_raises_value_error(self):
        with pytest.raises(ValueError):
            RagChunkSearchFactory().create("dijkstra", chunk_chars = 100, min_chars = 0)
