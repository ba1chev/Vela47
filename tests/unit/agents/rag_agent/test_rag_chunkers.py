import random
import pytest
import itertools

from app.intelligence.agents import RagChunkerType
from app.intelligence.agents import RagChunkerFixed
from app.intelligence.agents import RagChunkersFactory
from app.intelligence.agents import RagChunkerSemantic
from app.intelligence.agents import RagChunkerRecursive
from app.intelligence.agents import RAG_CHUNKERS_REGISTRY
from tests.fixtures.model.fake_embeddings import FakeEmbeddings

PARAGRAPHS = "\n\n".join(f"Paragraph {index} says something worth reading about topic {index}." for index in range(12))
SERVERS = (
    "The cluster runs the server on one instance. The server instance sits in the cluster subnet. "
    "The cluster restarts the server instance on failure. Every server instance in the cluster logs to one group."
)
BAKING = (
    "Mix the flour with sugar and butter. The butter and sugar melt before the flour goes in. "
    "Bake the flour dough until the sugar browns. Serve the butter cake once the sugar cools."
)


def make_semantic(**kwargs):
    return RagChunkerSemantic(FakeEmbeddings(), **kwargs)


def path_cost(starts, count, cut_costs, extend_costs):
    total = 0.0
    for start, end in zip(starts, starts[1:] + [count]):
        total += (cut_costs[start] if start else 0.0) + sum(extend_costs[(start, index)] for index in range(start + 1, end))
    return total


def allowed(starts, lengths, chunker):
    remaining = [sum(lengths[index:]) for index in range(len(lengths) + 1)]
    for start, end in zip(starts, starts[1:] + [len(lengths)]):
        if sum(lengths[start:end]) > chunker._chunk_chars:
            return False
        chars = sum(lengths[start:end])
        if end < len(lengths):
            forced = chars + lengths[end] > chunker._chunk_chars
            if not forced and (chars < chunker._min_chars or remaining[end] < chunker._min_chars):
                return False
    return True


class TestRagChunkerRecursive:
    def test_short_text_is_one_chunk(self):
        assert RagChunkerRecursive().chunk("  just a line  ") == ["just a line"]

    def test_empty_text_is_no_chunk(self):
        assert RagChunkerRecursive().chunk("   \n\n ") == []

    def test_no_chunk_is_longer_than_allowed(self):
        chunks = RagChunkerRecursive(chunk_chars = 120, overlap_chars = 30).chunk(PARAGRAPHS)
        assert len(chunks) > 1 and all(len(current) <= 120 for current in chunks)

    def test_the_overlap_never_pushes_a_chunk_past_the_limit(self):
        text = "x" * 150 + ". " + "y" * 30 + ". " + "z" * 190
        chunks = RagChunkerRecursive(chunk_chars = 200, overlap_chars = 40).chunk(text)
        assert all(len(current) <= 200 for current in chunks)

    def test_paragraphs_that_fit_are_never_cut(self):
        chunks = RagChunkerRecursive(chunk_chars = 200, overlap_chars = 0).chunk(PARAGRAPHS)
        for index in range(12):
            sentence = f"Paragraph {index} says something worth reading about topic {index}."
            assert any(sentence in current for current in chunks)

    def test_consecutive_chunks_overlap(self):
        chunks = RagChunkerRecursive(chunk_chars = 140, overlap_chars = 70).chunk(PARAGRAPHS)
        assert any(chunks[index].split("\n\n")[-1] in chunks[index + 1] for index in range(len(chunks) - 1))

    def test_every_chunk_is_a_verbatim_slice_of_the_document(self):
        for current in RagChunkerRecursive(chunk_chars = 90, overlap_chars = 20).chunk(PARAGRAPHS):
            assert current in PARAGRAPHS

    def test_a_single_unbroken_word_is_cut_at_the_limit(self):
        assert all(len(current) <= 50 for current in RagChunkerRecursive(chunk_chars = 50, overlap_chars = 0).chunk("x" * 175))


class TestRagChunkerFixed:
    def test_windows_have_the_set_width_and_overlap(self):
        chunks = RagChunkerFixed(chunk_chars = 10, overlap_chars = 4).chunk("abcdefghijklmnopqrstuvwxyz")
        assert chunks[0] == "abcdefghij" and chunks[1].startswith("ghij")

    def test_the_whole_text_is_covered(self):
        text = "abcdefghijklmnopqrstuvwxyz"
        assert RagChunkerFixed(chunk_chars = 10, overlap_chars = 4).chunk(text)[-1].endswith("z")


class TestRagChunkerSemantic:
    def test_empty_text_is_no_chunk_and_no_embedding_call(self):
        chunker = make_semantic()
        assert chunker.chunk("  \n ") == [] and chunker._embeddings.calls == []

    def test_one_sentence_is_one_chunk_without_an_embedding_call(self):
        chunker = make_semantic()
        assert chunker.chunk("  Just one sentence.  ") == ["Just one sentence."] and chunker._embeddings.calls == []

    def test_every_sentence_is_embedded_in_one_call(self):
        chunker = make_semantic(chunk_chars = 1000, min_chars = 60)
        chunker.chunk(SERVERS + " " + BAKING)
        assert len(chunker._embeddings.calls) == 1 and len(chunker._embeddings.calls[0]) == 8

    def test_the_cut_falls_where_the_topic_changes(self):
        chunker = make_semantic(chunk_chars = 1000, min_chars = 60, extend_weight = 3.0)
        assert chunker.chunk(SERVERS + " " + BAKING) == [SERVERS, BAKING]

    def test_a_forced_cut_prefers_a_paragraph_break(self):
        sentences = SERVERS.split(". ")
        text = ". ".join(sentences[:2]) + ".\n\n" + ". ".join(sentences[2:])
        chunks = make_semantic(chunk_chars = len(text) - 20, min_chars = 20).chunk(text)
        assert chunks == text.split("\n\n")

    def test_chunks_are_verbatim_slices_within_the_limits(self):
        text = "\n\n".join([SERVERS, BAKING] * 4)
        chunks = make_semantic(chunk_chars = 300, min_chars = 120).chunk(text)
        assert len(chunks) > 1 and all(current in text and len(current) <= 300 for current in chunks)
        assert all(len(current) >= 120 for current in chunks)

    def test_a_sentence_longer_than_a_chunk_is_cut_at_spaces(self):
        text = " ".join(["word"] * 60) + ". Short end."
        chunks = make_semantic(chunk_chars = 100, min_chars = 0).chunk(text)
        assert all(len(current) <= 100 for current in chunks) and "".join(chunks).replace(" ", "") == text.replace(" ", "")

    def test_the_search_finds_the_cheapest_allowed_cut(self):
        chunker = make_semantic(chunk_chars = 150, min_chars = 40)
        generator = random.Random(7)
        for _ in range(40):
            lengths = [generator.randint(15, 80) for _ in range(9)]
            cut_costs = [0.0] + [generator.uniform(0.0, 2.0) for _ in range(8)]
            extend_costs = {
                (start, index): generator.uniform(0.0, 1.0)
                for start in range(9) for index in range(start + 1, 9)
                if sum(lengths[start:index + 1]) <= 150
            }
            found = chunker._search(lengths, cut_costs, extend_costs)
            candidates = [
                [0, *middle] for size in range(9) for middle in itertools.combinations(range(1, 9), size)
                if allowed([0, *middle], lengths, chunker)
            ]
            cheapest = min(path_cost(current, 9, cut_costs, extend_costs) for current in candidates)
            assert allowed(found, lengths, chunker) and path_cost(found, 9, cut_costs, extend_costs) == pytest.approx(cheapest)


class TestRagChunkerParameters:
    def test_an_overlap_as_long_as_a_chunk_is_refused(self):
        with pytest.raises(ValueError):
            RagChunkerRecursive(chunk_chars = 100, overlap_chars = 100)

    def test_a_non_positive_chunk_length_is_refused(self):
        with pytest.raises(ValueError):
            RagChunkerFixed(chunk_chars = 0, overlap_chars = 0)

    def test_a_shortest_chunk_longer_than_the_longest_is_refused(self):
        with pytest.raises(ValueError):
            make_semantic(chunk_chars = 100, min_chars = 101)

    def test_a_negative_weight_is_refused(self):
        with pytest.raises(ValueError):
            make_semantic(cut_fee = -1.0)


class TestRagChunkersFactory:
    def test_every_type_is_registered(self):
        assert set(RAG_CHUNKERS_REGISTRY) == set(RagChunkerType)

    def test_it_builds_each_type_with_forwarded_arguments(self):
        chunker = RagChunkersFactory().create(RagChunkerType.FIXED, chunk_chars = 10, overlap_chars = 0)
        assert chunker.chunker_type is RagChunkerType.FIXED and chunker.chunk("a" * 25) == ["a" * 10, "a" * 10, "a" * 5]

    def test_it_builds_the_semantic_chunker_with_its_embeddings(self):
        embeddings = FakeEmbeddings()
        chunker = RagChunkersFactory().create(RagChunkerType.SEMANTIC, embeddings = embeddings)
        assert chunker.chunker_type is RagChunkerType.SEMANTIC and chunker._embeddings is embeddings

    def test_an_unknown_type_raises_value_error(self):
        with pytest.raises(ValueError):
            RagChunkersFactory().create("sentences")
