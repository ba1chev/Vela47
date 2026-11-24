from typing import Optional

from app.intelligence.model import ModelEmbeddings
from app.intelligence.model import ModelClientType
from app.intelligence.model import ModelClientBase
from app.server.builders import MODEL_CLIENT_TYPES
from app.server.builders import EMBEDDING_MODEL_NAMES
from app.intelligence.model import ModelClientsFactory
from app.intelligence.agents import RAG_TOPIC_REGISTER
from app.intelligence.agents import RagTopicRegisterWriter
from app.server.config_environment import ConfigEnvironment

TOPIC_REGISTER_AWS_REGION = "eu-central-1"
TOPIC_QUERY_TEMPLATES = {
    ConfigEnvironment.DEV: "Instruct: Given a topic, retrieve passages that are about it\nQuery: {query}",
    ConfigEnvironment.PROD: "{query}"
}


def topic_register_client(environment: ConfigEnvironment) -> ModelClientBase:
    client_type = MODEL_CLIENT_TYPES[environment]
    if client_type is ModelClientType.BEDROCK:
        return ModelClientsFactory().create(client_type, region_name = TOPIC_REGISTER_AWS_REGION)
    return ModelClientsFactory().create(client_type)


def build_topic_register(environments: Optional[list[ConfigEnvironment]] = None) -> None:
    chosen = environments if environments is not None else list(ConfigEnvironment)
    embeddings = [
        ModelEmbeddings(EMBEDDING_MODEL_NAMES[current_environment], client = topic_register_client(current_environment))
        for current_environment in chosen
    ]
    query_templates = {
        EMBEDDING_MODEL_NAMES[current_environment]: TOPIC_QUERY_TEMPLATES[current_environment]
        for current_environment in chosen
    }
    RagTopicRegisterWriter(embeddings, query_templates).write(RAG_TOPIC_REGISTER)
