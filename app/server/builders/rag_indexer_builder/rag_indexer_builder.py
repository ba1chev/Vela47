from app.intelligence.agents import RagIndexer
from app.intelligence.agents import RagChunkerType
from app.intelligence.model import ModelEmbeddings
from app.server.builders import EMBEDDING_MODEL_NAME
from app.intelligence.agents import RagChunkersFactory


def build_rag_indexer() -> RagIndexer:
    return RagIndexer(
        RagChunkersFactory().create(RagChunkerType.RECURSIVE),
        ModelEmbeddings(EMBEDDING_MODEL_NAME)
    )
