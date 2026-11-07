from app.intelligence.agents import RagIndexer
from app.intelligence.messages import MessageType
from app.intelligence.agents import RagChunkerRecursive
from tests.fixtures.model.fake_embeddings import FakeEmbeddings


def make_indexer(embeddings):
    return RagIndexer(RagChunkerRecursive(chunk_chars = 60, overlap_chars = 0), embeddings)


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
        assert entry.message.additional_kwargs == {"document_id": "d1", "chunk_index": 1}
        assert entry.message.type is MessageType.SYSTEM_MESSAGE

    def test_an_empty_document_costs_no_embedding_call(self):
        embeddings = FakeEmbeddings()
        assert make_indexer(embeddings).index("d1", "empty.md", "   ") == [] and embeddings.calls == []
