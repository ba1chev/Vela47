import re
import pathlib

from app.server.builders import build_model_client
from app.server.builders import MODEL_CLIENT_TYPES
from app.intelligence.model import ModelClientType
from app.intelligence.model import ModelClientOllama
from app.intelligence.model import ModelClientBedrock
from app.server.config_platform import ConfigPlatform

LOCAL_VARIABLES = (
    pathlib.Path(__file__).resolve().parents[4] / "deploy" / "terraform" / "environments" / "local" / "docker" / "variables.tf"
)


def offered_model_clients():
    block = re.search(r'variable "model_client" \{.*?contains\(\[(.*?)\]', LOCAL_VARIABLES.read_text(), re.DOTALL)
    return set(re.findall(r'"([^"]+)"', block.group(1)))


class LocalConfig:
    platform = ConfigPlatform.LOCAL
    model_client_type = None
    aws_region = None


class LocalBedrockConfig:
    platform = ConfigPlatform.LOCAL
    model_client_type = ModelClientType.BEDROCK
    aws_region = "eu-central-1"


class AwsConfig:
    platform = ConfigPlatform.AWS
    model_client_type = None
    aws_region = "eu-central-1"


class TestModelClientBuilder:
    def test_every_platform_has_a_backend(self):
        assert set(MODEL_CLIENT_TYPES) == set(ConfigPlatform)

    def test_local_runs_on_ollama(self):
        assert isinstance(build_model_client(LocalConfig()), ModelClientOllama)

    def test_aws_runs_on_bedrock_in_its_region(self):
        client = build_model_client(AwsConfig())
        assert isinstance(client, ModelClientBedrock) and client._runtime.meta.region_name == "eu-central-1"

    def test_local_may_choose_bedrock_in_its_region(self):
        client = build_model_client(LocalBedrockConfig())
        assert isinstance(client, ModelClientBedrock) and client._runtime.meta.region_name == "eu-central-1"

    def test_the_local_environment_offers_exactly_the_backends_the_server_knows(self):
        assert offered_model_clients() == {current.value for current in ModelClientType}
