from app.intelligence.model import ModelConfig
from app.intelligence.messages import MessageHuman
from app.intelligence.model import ModelEmbeddings
from app.intelligence.model import ModelFoundation
from app.intelligence.tracing import TracingService
from app.intelligence.tracing import TraceEventType
from app.intelligence.model import ModelClientOllama
from tests.fixtures.model.scripted_model_client import ScriptedModelClient


def reported(tracer):
    return [current.payload for current in tracer.events() if current.type is TraceEventType.MODEL_INVOKED]


class TestModelFoundation:
    def test_without_a_client_it_runs_on_ollama(self):
        assert isinstance(ModelFoundation(ModelConfig(model_name = "qwen3:1.7b"))._client, ModelClientOllama)

    def test_invoke_hands_its_config_to_the_client_and_returns_the_reply(self):
        client = ScriptedModelClient()
        reply = ModelFoundation(ModelConfig(model_name = "m"), client = client).invoke([MessageHuman(content = "hi")], output_schema = {"type": "object"})
        assert reply.content == "hello" and client.calls == [("chat", "m", 1, None, {"type": "object"})]

    def test_every_invoke_is_reported_with_its_usage_whatever_the_backend(self):
        tracer = TracingService()
        ModelFoundation(ModelConfig(model_name = "m"), tracer, ScriptedModelClient()).invoke([MessageHuman(content = "hi")])
        payload = reported(tracer)[0]
        assert (payload["input_tokens"], payload["output_tokens"], payload["total_tokens"]) == (7, 2, 9)
        assert payload["tool_calls"] == ["read_file"]

    def test_a_stream_yields_only_text_and_is_reported_once_it_ends(self):
        tracer = TracingService()
        pieces = list(ModelFoundation(ModelConfig(model_name = "m"), tracer, ScriptedModelClient()).stream([MessageHuman(content = "hi")]))
        assert pieces == ["one ", "two"]
        assert reported(tracer)[0]["total_tokens"] == 7 and reported(tracer)[0]["streamed"]


class TestModelEmbeddings:
    def test_texts_reach_the_client_in_batches(self):
        client = ScriptedModelClient()
        vectors = ModelEmbeddings("e", client = client).embed_many([str(index) * 2 for index in range(ModelEmbeddings.BATCH_SIZE + 1)])
        assert len(vectors) == ModelEmbeddings.BATCH_SIZE + 1
        assert [len(current[2]) for current in client.calls] == [ModelEmbeddings.BATCH_SIZE, 1]

    def test_every_batch_is_reported(self):
        tracer = TracingService()
        ModelEmbeddings("e", tracer, client = ScriptedModelClient()).embed("hello")
        assert reported(tracer)[0]["embedding"] and reported(tracer)[0]["input_tokens"] == 1
