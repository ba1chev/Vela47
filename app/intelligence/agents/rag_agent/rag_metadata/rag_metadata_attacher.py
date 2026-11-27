from typing import Any
from collections import Counter

from app.intelligence.agents import RagTopicIndex
from app.intelligence.model import ModelEmbeddings
from app.intelligence.agents import RagMetadataType
from app.intelligence.tracing import describe_numbers
from app.intelligence.agents import RagMetadataDocument
from app.intelligence.memory import VectorDbMemorySource
from app.intelligence.memory import VectorDbMemoryMetadata
from app.intelligence.agents import RagMetadataExtractorBase
from app.intelligence.tracing import current_tracing_service
from app.intelligence.agents import RagMetadataExtractorsFactory


class RagMetadataAttacher:
    """Works out the metadata every chunk's vector carries, once, when its document is
    indexed. It places each chunk in the text first — chunks are verbatim slices, so
    the source span is where the chunk is found after the previous one starts — then
    runs the extractors EXTRACTOR_TYPES names one after another, each filling its own
    field, the way VectorDbOperationManager runs operations.

    The topic reuses the chunk's vector and the section is read from the text; only
    keywords call the embedding model, once per document, for their candidate words.
    Each extractor is traced as a step with a summary of what it filled in."""

    EXTRACTOR_TYPES = (RagMetadataType.SECTION, RagMetadataType.TOPIC, RagMetadataType.KEYWORDS)

    def __init__(self, topic_index: RagTopicIndex, embeddings: ModelEmbeddings, max_keywords: int = 5) -> None:
        arguments = {
            RagMetadataType.SECTION: {},
            RagMetadataType.TOPIC: {"topic_index": topic_index},
            RagMetadataType.KEYWORDS: {"embeddings": embeddings, "max_keywords": max_keywords}
        }
        factory = RagMetadataExtractorsFactory()
        self._extractors: list[RagMetadataExtractorBase] = [
            factory.create(current_type, **arguments[current_type])
            for current_type in self.EXTRACTOR_TYPES
        ]

    def _sources(self, document: RagMetadataDocument) -> list[VectorDbMemorySource]:
        sources: list[VectorDbMemorySource] = []
        cursor = 0
        for index, current_chunk in enumerate(document.chunks):
            start = document.text.find(current_chunk, cursor)
            if start < 0:
                start = document.text.find(current_chunk)
            span = {"start": start, "end": start + len(current_chunk)} if start >= 0 else {}
            sources.append(VectorDbMemorySource(
                document_id = document.document_id, title = document.title, chunk_index = index, **span
            ))
            cursor = start + 1 if start >= 0 else cursor
        return sources

    def _summary(self, metadata_type: RagMetadataType, metadata: list[VectorDbMemoryMetadata]) -> dict[str, Any]:
        if metadata_type is RagMetadataType.SECTION:
            sections = [current.section for current in metadata if current.section]
            return {
                "detail": f"{len(sections)} of {len(metadata)} chunks under a heading, {len(set(sections))} sections",
                "sections": list(dict.fromkeys(sections))
            }
        if metadata_type is RagMetadataType.TOPIC:
            topics = Counter(current.topic for current in metadata if current.topic)
            scores = [current.topic_score for current in metadata if current.topic_score is not None]
            return {
                "detail": ", ".join(f"{current_topic} ×{current_count}" for current_topic, current_count in topics.most_common(3)),
                "topics": dict(topics.most_common()),
                "score": describe_numbers(scores)
            }
        keywords = [current_keyword for current in metadata for current_keyword in current.keywords]
        return {
            "detail": f"{len(keywords)} keywords, {len(set(keywords))} distinct",
            "keywords": [current.keywords for current in metadata]
        }

    def attach(self, document: RagMetadataDocument) -> list[VectorDbMemoryMetadata]:
        tracer = current_tracing_service()
        metadata = [VectorDbMemoryMetadata(source = current_source) for current_source in self._sources(document)]
        placed = sum(current.source.start is not None for current in metadata)
        tracer.record("Placement", "metadata", {
            "detail": f"{placed} of {len(metadata)} chunks found verbatim in the text",
            "spans": [[current.source.start, current.source.end] for current in metadata]
        })
        for current_extractor in self._extractors:
            with tracer.step(current_extractor.metadata_type.name.title(), "metadata", {
                "extractor": type(current_extractor).__name__
            }) as span:
                metadata = current_extractor.apply(document, metadata)
                span.update(self._summary(current_extractor.metadata_type, metadata))
        return metadata
