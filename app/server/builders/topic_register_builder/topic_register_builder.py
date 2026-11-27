from typing import Optional

from app.intelligence.model import ModelEmbeddings
from app.intelligence.model import ModelClientType
from app.intelligence.model import ModelClientBase
from app.server.builders import EMBEDDING_MODEL_NAMES
from app.intelligence.model import ModelClientsFactory
from app.intelligence.agents import RAG_TOPIC_REGISTER
from app.intelligence.agents import RagTopicRegisterWriter

TOPIC_REGISTER_AWS_REGION = "eu-central-1"
TOPIC_QUERY_TEMPLATES = {
    ModelClientType.OLLAMA: "Instruct: Given a topic, retrieve passages that are about it\nQuery: {query}",
    ModelClientType.BEDROCK: "{query}"
}


def topic_register_client(client_type: ModelClientType) -> ModelClientBase:
    if client_type is ModelClientType.BEDROCK:
        return ModelClientsFactory().create(client_type, region_name = TOPIC_REGISTER_AWS_REGION)
    return ModelClientsFactory().create(client_type)


def build_topic_register(client_types: Optional[list[ModelClientType]] = None) -> None:
    chosen = client_types if client_types is not None else list(ModelClientType)
    embeddings = [
        ModelEmbeddings(EMBEDDING_MODEL_NAMES[current_type], client = topic_register_client(current_type))
        for current_type in chosen
    ]
    query_templates = {
        EMBEDDING_MODEL_NAMES[current_type]: TOPIC_QUERY_TEMPLATES[current_type]
        for current_type in chosen
    }
    RagTopicRegisterWriter(embeddings, query_templates).write(RAG_TOPIC_REGISTER)
