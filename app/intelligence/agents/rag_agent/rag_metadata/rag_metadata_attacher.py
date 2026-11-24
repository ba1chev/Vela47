from app.intelligence.agents import RagTopicIndex
from app.intelligence.model import ModelEmbeddings
from app.intelligence.agents import RagMetadataType
from app.intelligence.agents import RagMetadataDocument
from app.intelligence.memory import VectorDbMemorySource
from app.intelligence.memory import VectorDbMemoryMetadata
from app.intelligence.agents import RagMetadataExtractorBase
from app.intelligence.agents import RagMetadataExtractorsFactory


class RagMetadataAttacher:
    """Works out the metadata every chunk's vector carries, once, when its document is
    indexed. It places each chunk in the text first — chunks are verbatim slices, so
    the source span is where the chunk is found after the previous one starts — then
    runs the extractors EXTRACTOR_TYPES names one after another, each filling its own
    field, the way VectorDbOperationManager runs operations.

    The topic reuses the chunk's vector and the section is read from the text; only
    keywords call the embedding model, once per document, for their candidate words."""

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

    def attach(self, document: RagMetadataDocument) -> list[VectorDbMemoryMetadata]:
        metadata = [VectorDbMemoryMetadata(source = current_source) for current_source in self._sources(document)]
        for current_extractor in self._extractors:
            metadata = current_extractor.apply(document, metadata)
        return metadata
