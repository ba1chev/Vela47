import pytest
from pydantic import ValidationError

from app.intelligence.messages import MessageSystem
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.memory import VectorDbMemorySource
from app.intelligence.memory import VectorDbMemoryMetadata


def make_source(**fields):
    return VectorDbMemorySource(**{"document_id": "d1", "title": "guide.md", "chunk_index": 0, **fields})


class TestVectorDbMemoryMetadata:
    def test_an_entry_carries_no_metadata_unless_given_some(self):
        assert VectorDbMemoryEntry(message = MessageSystem(content = "text"), vector = [1.0]).metadata is None

    def test_only_the_source_is_required(self):
        metadata = VectorDbMemoryMetadata(source = make_source())
        assert (metadata.section, metadata.topic, metadata.topic_score, metadata.keywords) == (None, None, None, [])

    def test_a_source_may_have_no_span(self):
        assert (make_source().start, make_source().end) == (None, None)

    def test_a_negative_position_is_refused(self):
        for current in ({"chunk_index": -1}, {"start": -1}):
            with pytest.raises(ValidationError):
                make_source(**current)

    def test_metadata_cannot_be_changed_once_made(self):
        metadata = VectorDbMemoryMetadata(source = make_source())
        with pytest.raises(ValidationError):
            metadata.topic = "Databases"

    def test_an_entry_keeps_its_metadata(self):
        metadata = VectorDbMemoryMetadata(source = make_source(start = 0, end = 4), keywords = ["text"])
        entry = VectorDbMemoryEntry(message = MessageSystem(content = "text"), vector = [1.0], metadata = metadata)
        assert entry.metadata == metadata
