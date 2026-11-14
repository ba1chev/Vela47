from app.server.builders import build_model_client
from app.server.builders import MODEL_CLIENT_TYPES
from app.intelligence.model import ModelClientOllama
from app.intelligence.model import ModelClientBedrock
from app.server.config_environment import ConfigEnvironment


class DevConfig:
    environment = ConfigEnvironment.DEV
    aws_region = None


class ProdConfig:
    environment = ConfigEnvironment.PROD
    aws_region = "eu-central-1"


class TestModelClientBuilder:
    def test_every_environment_has_a_backend(self):
        assert set(MODEL_CLIENT_TYPES) == set(ConfigEnvironment)

    def test_development_runs_on_ollama(self):
        assert isinstance(build_model_client(DevConfig()), ModelClientOllama)

    def test_production_runs_on_bedrock_in_its_region(self):
        client = build_model_client(ProdConfig())
        assert isinstance(client, ModelClientBedrock) and client._runtime.meta.region_name == "eu-central-1"
