from app.intelligence.agents import RagIndexer
from app.intelligence.messages import MessageType
from app.intelligence.tracing import TraceEventType
from app.intelligence.tracing import TracingService
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


class TestRagIndexerTrace:
    def traced(self):
        tracer = TracingService()
        with tracer.step("Upload", "ingest"):
            make_indexer(FakeEmbeddings()).index("d1", "guide.md", TEXT)
        return tracer.events()

    def test_chunking_embedding_and_metadata_are_layers(self):
        layers = [current.label for current in self.traced() if current.type is TraceEventType.LAYER_FINISHED]
        assert layers == ["Chunking", "Embedding", "Metadata"]

    def test_each_extractor_is_a_step_with_a_summary(self):
        steps = {current.label: current.payload for current in self.traced() if current.type is TraceEventType.STEP_FINISHED}
        assert steps["Section"]["extractor"] == "RagMetadataExtractorSection"
        assert sum(steps["Topic"]["topics"].values()) == 3
        assert len(steps["Keywords"]["keywords"]) == 3

    def test_the_chunk_table_holds_every_chunk_whole(self):
        (table,) = [current for current in self.traced() if current.label == "Chunk table"]
        assert [current["text"] for current in table.payload["rows"]] == [
            "First paragraph about deployment.", "Second paragraph about backups.", "Third paragraph about errors."
        ]
        assert table.payload["rows"][1]["start"] == TEXT.index("Second")
