import pytest

from app.intelligence.model import ModelClientType
from app.intelligence.model import ModelClientOllama
from app.intelligence.model import ModelClientBedrock
from app.intelligence.model import ModelClientsFactory
from app.intelligence.model import MODEL_CLIENTS_REGISTRY
from tests.fixtures.model.stub_bedrock_runtime import StubBedrockRuntime


class TestModelClientsFactory:
    def test_every_type_is_registered(self):
        assert set(MODEL_CLIENTS_REGISTRY) == set(ModelClientType)

    def test_ollama_needs_nothing(self):
        assert isinstance(ModelClientsFactory().create(ModelClientType.OLLAMA), ModelClientOllama)

    def test_bedrock_is_given_its_region(self):
        client = ModelClientsFactory().create(ModelClientType.BEDROCK, region_name = "eu-central-1", runtime = StubBedrockRuntime())
        assert isinstance(client, ModelClientBedrock)

    def test_an_unknown_type_is_refused(self):
        with pytest.raises(ValueError, match = "No model client class registered"):
            ModelClientsFactory().create("carrier pigeon")
