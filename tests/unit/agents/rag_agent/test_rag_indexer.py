from app.intelligence.agents import RagIndexer
from app.intelligence.messages import MessageType
from app.intelligence.agents import RagChunkerRecursive
from app.intelligence.agents import RagMetadataAttacher
from app.intelligence.memory import VectorDbMemorySource
from tests.fixtures.model.fake_embeddings import FakeEmbeddings
from tests.fixtures.agents.fake_topic_register import FAKE_TOPIC_INDEX


def make_indexer(embeddings):
    return RagIndexer(
        RagChunkerRecursive(chunk_chars = 60, overlap_chars = 0),
        embeddings,
        RagMetadataAttacher(FAKE_TOPIC_INDEX, FakeEmbeddings())
    )


TEXT = "First paragraph about deployment.\n\nSecond paragraph about backups.\n\nThird paragraph about errors."


class TestRagIndexer:
    def test_every_chunk_becomes_an_entry_with_a_vector(self):
        entries = make_indexer(FakeEmbeddings()).index("d1", "guide.md", TEXT)
        assert len(entries) == 3 and all(len(current.vector) == FakeEmbeddings.DIMENSIONS for current in entries)

    def test_chunks_are_embedded_in_one_batch(self):
        embeddings = FakeEmbeddings()
        make_indexer(embeddings).index("d1", "guide.md", TEXT)
        assert len(embeddings.calls) == 1 and len(embeddings.calls[0]) == 3

    def test_each_entry_carries_its_identity(self):
        entry = make_indexer(FakeEmbeddings()).index("d1", "guide.md", TEXT)[1]
        assert entry.message.id == "d1-1"
        assert entry.message.name == "guide.md"
        assert entry.message.additional_kwargs == {}
        assert entry.message.type is MessageType.SYSTEM_MESSAGE

    def test_each_entry_carries_its_source_span_in_the_document(self):
        entry = make_indexer(FakeEmbeddings()).index("d1", "guide.md", TEXT)[1]
        start = TEXT.index("Second")
        assert entry.metadata.source == VectorDbMemorySource(
            document_id = "d1", title = "guide.md", chunk_index = 1, start = start, end = start + len(entry.message.content)
        )
        assert TEXT[entry.metadata.source.start:entry.metadata.source.end] == entry.message.content

    def test_each_entry_is_given_the_topic_of_its_own_vector_and_its_keywords(self):
        entry = make_indexer(FakeEmbeddings()).index("d1", "guide.md", TEXT)[1]
        assert (entry.metadata.topic, entry.metadata.topic_score) == FAKE_TOPIC_INDEX.nearest(entry.vector)
        assert "backups" in entry.metadata.keywords

    def test_an_empty_document_costs_no_embedding_call(self):
        embeddings = FakeEmbeddings()
        assert make_indexer(embeddings).index("d1", "empty.md", "   ") == [] and embeddings.calls == []
