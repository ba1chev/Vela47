from app.server.builders import build_model_client
from app.server.builders import MODEL_CLIENT_TYPES
from app.intelligence.model import ModelClientOllama
from app.intelligence.model import ModelClientBedrock
from app.server.config_platform import ConfigPlatform


class LocalConfig:
    platform = ConfigPlatform.LOCAL
    aws_region = None


class AwsConfig:
    platform = ConfigPlatform.AWS
    aws_region = "eu-central-1"


class TestModelClientBuilder:
    def test_every_platform_has_a_backend(self):
        assert set(MODEL_CLIENT_TYPES) == set(ConfigPlatform)

    def test_local_runs_on_ollama(self):
        assert isinstance(build_model_client(LocalConfig()), ModelClientOllama)

    def test_aws_runs_on_bedrock_in_its_region(self):
        client = build_model_client(AwsConfig())
        assert isinstance(client, ModelClientBedrock) and client._runtime.meta.region_name == "eu-central-1"
