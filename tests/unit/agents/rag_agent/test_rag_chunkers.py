import pytest

from app.intelligence.agents import RagChunkerType
from app.intelligence.agents import RagChunkerFixed
from app.intelligence.agents import RagChunkersFactory
from app.intelligence.agents import RagChunkerRecursive
from app.intelligence.agents import RAG_CHUNKERS_REGISTRY

PARAGRAPHS = "\n\n".join(f"Paragraph {index} says something worth reading about topic {index}." for index in range(12))


class TestRagChunkerRecursive:
    def test_short_text_is_one_chunk(self):
        assert RagChunkerRecursive().chunk("  just a line  ") == ["just a line"]

    def test_empty_text_is_no_chunk(self):
        assert RagChunkerRecursive().chunk("   \n\n ") == []

    def test_no_chunk_is_longer_than_allowed(self):
        chunks = RagChunkerRecursive(chunk_chars = 120, overlap_chars = 30).chunk(PARAGRAPHS)
        assert len(chunks) > 1 and all(len(current) <= 120 for current in chunks)

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


class TestRagChunkerParameters:
    def test_an_overlap_as_long_as_a_chunk_is_refused(self):
        with pytest.raises(ValueError):
            RagChunkerRecursive(chunk_chars = 100, overlap_chars = 100)

    def test_a_non_positive_chunk_length_is_refused(self):
        with pytest.raises(ValueError):
            RagChunkerFixed(chunk_chars = 0, overlap_chars = 0)


class TestRagChunkersFactory:
    def test_every_type_is_registered(self):
        assert set(RAG_CHUNKERS_REGISTRY) == set(RagChunkerType)

    def test_it_builds_each_type_with_forwarded_arguments(self):
        chunker = RagChunkersFactory().create(RagChunkerType.FIXED, chunk_chars = 10, overlap_chars = 0)
        assert chunker.chunker_type is RagChunkerType.FIXED and chunker.chunk("a" * 25) == ["a" * 10, "a" * 10, "a" * 5]

    def test_an_unknown_type_raises_value_error(self):
        with pytest.raises(ValueError):
            RagChunkersFactory().create("semantic")
