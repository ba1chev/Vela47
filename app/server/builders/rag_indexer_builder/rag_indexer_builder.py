from app.intelligence.agents import RagIndexer
from app.intelligence.agents import RagChunkerType
from app.intelligence.model import ModelEmbeddings
from app.server.builders import EMBEDDING_MODEL_NAME
from app.intelligence.agents import RagChunkersFactory


def build_rag_indexer() -> RagIndexer:
    """Assembles the indexer uploads go through: the recursive chunker, which follows a
    document's own paragraphs and sentences, and the same embedding model the RAG agent
    searches with. The two must match — vectors from different models cannot be
    compared — which is why the model name is the RAG agent builder's, not a second copy.

    Built once for the process, unlike the agent: it holds no run's state and reports to
    no run's tracer, since an upload is not part of a conversation."""
    return RagIndexer(
        RagChunkersFactory().create(RagChunkerType.RECURSIVE),
        ModelEmbeddings(EMBEDDING_MODEL_NAME)
    )
