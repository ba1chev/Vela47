from app.server.config import Config
from app.intelligence.model import ModelClientType
from app.intelligence.model import ModelClientBase
from app.server.config_platform import ConfigPlatform
from app.intelligence.model import ModelClientsFactory

MODEL_CLIENT_TYPES = {
    ConfigPlatform.LOCAL: ModelClientType.OLLAMA,
    ConfigPlatform.AWS: ModelClientType.BEDROCK
}


def build_model_client(config: Config) -> ModelClientBase:
    client_type = config.model_client_type or MODEL_CLIENT_TYPES[config.platform]
    if client_type is ModelClientType.BEDROCK:
        return ModelClientsFactory().create(client_type, region_name = config.aws_region)
    return ModelClientsFactory().create(client_type)
