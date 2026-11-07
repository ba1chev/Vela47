from app.intelligence.agents import RagChunkerBase
from app.intelligence.model import ModelEmbeddings
from app.intelligence.messages import MessageSystem
from app.intelligence.memory import VectorDbMemoryEntry


class RagIndexer:
    """Turns a document into the entries the RAG agent searches: cut by a chunker,
    embedded in batches, and wrapped as VectorDbMemoryEntry. The ingestion half of
    retrieval-augmented generation, kept beside the agent that reads what it writes so
    the two cannot disagree about what a chunk looks like.

    Each chunk becomes a MessageSystem — a retrieved passage reaches the model as
    context, which is what a system message is — and carries its identity in fields the
    framework already has: id is '<document id>-<position>', name is the document's
    title, and additional_kwargs holds document_id and chunk_index. Nothing in the vector
    store had to change for it to hold documents."""

    def __init__(self, chunker: RagChunkerBase, embeddings: ModelEmbeddings) -> None:
        self._chunker: RagChunkerBase = chunker
        self._embeddings: ModelEmbeddings = embeddings

    def index(self, document_id: str, title: str, text: str) -> list[VectorDbMemoryEntry]:
        chunks = self._chunker.chunk(text)
        vectors = self._embeddings.embed_many(chunks) if chunks else []

        return [
            VectorDbMemoryEntry(
                message = MessageSystem(
                    content = current_chunk,
                    id = f"{document_id}-{index}",
                    name = title,
                    additional_kwargs = {"document_id": document_id, "chunk_index": index}
                ),
                vector = current_vector
            )
            for index, (current_chunk, current_vector) in enumerate(zip(chunks, vectors))
        ]
