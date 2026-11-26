from typing import Optional

from app.intelligence.model import ModelEmbeddings
from app.intelligence.model import ModelClientType
from app.intelligence.model import ModelClientBase
from app.server.builders import MODEL_CLIENT_TYPES
from app.server.builders import EMBEDDING_MODEL_NAMES
from app.server.config_platform import ConfigPlatform
from app.intelligence.model import ModelClientsFactory
from app.intelligence.agents import RAG_TOPIC_REGISTER
from app.intelligence.agents import RagTopicRegisterWriter

TOPIC_REGISTER_AWS_REGION = "eu-central-1"
TOPIC_QUERY_TEMPLATES = {
    ConfigPlatform.LOCAL: "Instruct: Given a topic, retrieve passages that are about it\nQuery: {query}",
    ConfigPlatform.AWS: "{query}"
}


def topic_register_client(platform: ConfigPlatform) -> ModelClientBase:
    client_type = MODEL_CLIENT_TYPES[platform]
    if client_type is ModelClientType.BEDROCK:
        return ModelClientsFactory().create(client_type, region_name = TOPIC_REGISTER_AWS_REGION)
    return ModelClientsFactory().create(client_type)


def build_topic_register(platforms: Optional[list[ConfigPlatform]] = None) -> None:
    chosen = platforms if platforms is not None else list(ConfigPlatform)
    embeddings = [
        ModelEmbeddings(EMBEDDING_MODEL_NAMES[current_platform], client = topic_register_client(current_platform))
        for current_platform in chosen
    ]
    query_templates = {
        EMBEDDING_MODEL_NAMES[current_platform]: TOPIC_QUERY_TEMPLATES[current_platform]
        for current_platform in chosen
    }
    RagTopicRegisterWriter(embeddings, query_templates).write(RAG_TOPIC_REGISTER)
