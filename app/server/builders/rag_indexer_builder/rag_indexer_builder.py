from app.intelligence.agents import RagIndexer
from app.intelligence.agents import RagTopicIndex
from app.intelligence.agents import RagChunkerType
from app.intelligence.model import ModelEmbeddings
from app.intelligence.model import ModelClientBase
from app.server.builders import EMBEDDING_MODEL_NAMES
from app.intelligence.agents import RagChunkersFactory
from app.intelligence.agents import RAG_TOPIC_REGISTER
from app.intelligence.agents import RagMetadataAttacher
from app.server.config_environment import ConfigEnvironment


def build_rag_indexer(environment: ConfigEnvironment, model_client: ModelClientBase) -> RagIndexer:
    embeddings = ModelEmbeddings(EMBEDDING_MODEL_NAMES[environment], client = model_client)
    chunker = RagChunkersFactory().create(RagChunkerType.SEMANTIC, embeddings = embeddings)
    metadata_attacher = RagMetadataAttacher(RagTopicIndex(RAG_TOPIC_REGISTER, embeddings.model_name), embeddings)
    return RagIndexer(chunker, embeddings, metadata_attacher)
