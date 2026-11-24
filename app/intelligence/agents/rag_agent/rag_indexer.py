from app.intelligence.agents import RagChunkerBase
from app.intelligence.model import ModelEmbeddings
from app.intelligence.messages import MessageSystem
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.agents import RagMetadataAttacher
from app.intelligence.agents import RagMetadataDocument


class RagIndexer:
    """Turns a document into the entries the RAG agent searches: cut by a chunker,
    embedded in batches, described by a RagMetadataAttacher and wrapped as
    VectorDbMemoryEntry. The ingestion half of retrieval-augmented generation, kept
    beside the agent that reads what it writes so the two cannot disagree about what a
    chunk looks like.

    Each chunk becomes a MessageSystem — a retrieved passage reaches the model as
    context, which is what a system message is — with id '<document id>-<position>' and
    the document's title as its name. Everything else known about it, from its span in
    the document to its topic, travels as the entry's metadata."""

    def __init__(self, chunker: RagChunkerBase, embeddings: ModelEmbeddings,
        metadata_attacher: RagMetadataAttacher) -> None:
        self._chunker: RagChunkerBase = chunker
        self._embeddings: ModelEmbeddings = embeddings
        self._metadata_attacher: RagMetadataAttacher = metadata_attacher

    def index(self, document_id: str, title: str, text: str) -> list[VectorDbMemoryEntry]:
        chunks = self._chunker.chunk(text)
        if not chunks:
            return []

        vectors = self._embeddings.embed_many(chunks)
        metadata = self._metadata_attacher.attach(RagMetadataDocument(
            document_id = document_id, title = title, text = text, chunks = chunks, vectors = vectors
        ))

        return [
            VectorDbMemoryEntry(
                message = MessageSystem(content = current_chunk, id = f"{document_id}-{index}", name = title),
                vector = current_vector,
                metadata = current_metadata
            )
            for index, (current_chunk, current_vector, current_metadata) in enumerate(zip(chunks, vectors, metadata))
        ]
