from typing import Any
from contextlib import AbstractContextManager

from app.intelligence.agents import RagChunkerBase
from app.intelligence.model import ModelEmbeddings
from app.intelligence.tracing import TraceEventType
from app.intelligence.messages import MessageSystem
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.agents import RagMetadataAttacher
from app.intelligence.agents import RagMetadataDocument
from app.intelligence.tracing import current_tracing_service


class RagIndexer:
    """Turns a document into the entries the RAG agent searches: cut by a chunker,
    embedded in batches, described by a RagMetadataAttacher and wrapped as
    VectorDbMemoryEntry. The ingestion half of retrieval-augmented generation, kept
    beside the agent that reads what it writes so the two cannot disagree about what a
    chunk looks like.

    Each chunk becomes a MessageSystem — a retrieved passage reaches the model as
    context, which is what a system message is — with id '<document id>-<position>' and
    the document's title as its name. Everything else known about it, from its span in
    the document to its topic, travels as the entry's metadata. Chunking, embedding and
    metadata are each traced as a layer of the run that is indexing."""

    def __init__(self, chunker: RagChunkerBase, embeddings: ModelEmbeddings,
        metadata_attacher: RagMetadataAttacher) -> None:
        self._chunker: RagChunkerBase = chunker
        self._embeddings: ModelEmbeddings = embeddings
        self._metadata_attacher: RagMetadataAttacher = metadata_attacher

    def _layer(self, label: str, payload: dict[str, Any]) -> AbstractContextManager[dict[str, Any]]:
        return current_tracing_service().span(TraceEventType.LAYER_STARTED, TraceEventType.LAYER_FINISHED, label, payload)

    def index(self, document_id: str, title: str, text: str) -> list[VectorDbMemoryEntry]:
        with self._layer("Chunking", {"chunker": self._chunker.chunker_type.value}) as span:
            chunks = self._chunker.chunk(text)
            span["chunks"] = len(chunks)
            span["detail"] = f"{len(chunks)} chunks by the {self._chunker.chunker_type.value} chunker"
        if not chunks:
            return []

        with self._layer("Embedding", {"model": self._embeddings.model_name, "chunks": len(chunks)}) as span:
            vectors = self._embeddings.embed_many(chunks)
            span["dimensions"] = len(vectors[0])
            span["detail"] = f"{len(vectors)} chunks embedded by {self._embeddings.model_name}, {len(vectors[0])} dimensions"

        with self._layer("Metadata", {"chunks": len(chunks)}) as span:
            metadata = self._metadata_attacher.attach(RagMetadataDocument(
                document_id = document_id, title = title, text = text, chunks = chunks, vectors = vectors
            ))
            current_tracing_service().record("Chunk table", "metadata", {
                "detail": f"{len(chunks)} chunks with their span, section, topic and keywords",
                "rows": [
                    {
                        "index": index,
                        "characters": len(current_chunk),
                        "start": current_metadata.source.start,
                        "end": current_metadata.source.end,
                        "section": current_metadata.section,
                        "topic": current_metadata.topic,
                        "topic_score": round(current_metadata.topic_score, 4) if current_metadata.topic_score is not None else None,
                        "keywords": current_metadata.keywords,
                        "text": current_chunk
                    }
                    for index, (current_chunk, current_metadata) in enumerate(zip(chunks, metadata))
                ]
            })
            span["detail"] = "section, topic and keywords for every chunk"

        return [
            VectorDbMemoryEntry(
                message = MessageSystem(content = current_chunk, id = f"{document_id}-{index}", name = title),
                vector = current_vector,
                metadata = current_metadata
            )
            for index, (current_chunk, current_vector, current_metadata) in enumerate(zip(chunks, vectors, metadata))
        ]
