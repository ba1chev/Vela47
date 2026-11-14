from app.server.builders import KEEP_ALIVE
from app.intelligence.agents import RagIndexer
from app.intelligence.agents import RagChunkerType
from app.intelligence.model import ModelEmbeddings
from app.server.builders import EMBEDDING_MODEL_NAMES
from app.intelligence.agents import RagChunkersFactory
from app.server.config_environment import ConfigEnvironment


def build_rag_indexer(environment: ConfigEnvironment) -> RagIndexer:
    return RagIndexer(
        RagChunkersFactory().create(RagChunkerType.RECURSIVE),
        ModelEmbeddings(EMBEDDING_MODEL_NAMES[environment], keep_alive = KEEP_ALIVE[environment])
    )
