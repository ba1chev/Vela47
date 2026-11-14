from app.server.config import Config
from app.intelligence.model import ModelClientType
from app.intelligence.model import ModelClientBase
from app.intelligence.model import ModelClientsFactory
from app.server.config_environment import ConfigEnvironment

MODEL_CLIENT_TYPES = {
    ConfigEnvironment.DEV: ModelClientType.OLLAMA,
    ConfigEnvironment.PROD: ModelClientType.BEDROCK
}


def build_model_client(config: Config) -> ModelClientBase:
    client_type = MODEL_CLIENT_TYPES[config.environment]
    if client_type is ModelClientType.BEDROCK:
        return ModelClientsFactory().create(client_type, region_name = config.aws_region)
    return ModelClientsFactory().create(client_type)
