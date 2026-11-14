from app.intelligence.messages import MessageAI
from app.intelligence.model import ModelClientType
from app.intelligence.model import ModelClientBase
from app.intelligence.messages import MessageToolCall
from app.intelligence.messages import MessageUsageMetadata


class ScriptedModelClient(ModelClientBase):
    """A backend that answers from fixed values and records what it was asked, so the
    tracing and accounting ModelFoundation and ModelEmbeddings do around any backend can
    be tested alone."""

    def __init__(self) -> None:
        self.calls = []

    @property
    def client_type(self):
        return ModelClientType.OLLAMA

    def chat(self, config, messages, tools = None, output_schema = None):
        self.calls.append(("chat", config.model_name, len(messages), tools, output_schema))
        return MessageAI(
            content = "hello",
            tool_calls = [MessageToolCall(name = "read_file", args = {"path": "a.py"}, id = "c1")],
            usage_metadata = MessageUsageMetadata(input_tokens = 7, output_tokens = 2, total_tokens = 9)
        )

    def stream(self, config, messages):
        self.calls.append(("stream", config.model_name, len(messages)))
        yield MessageAI(content = "one ")
        yield MessageAI(content = "two")
        yield MessageAI(content = "", usage_metadata = MessageUsageMetadata(input_tokens = 5, output_tokens = 2, total_tokens = 7))

    def embed(self, model_name, texts, keep_alive):
        self.calls.append(("embed", model_name, list(texts), keep_alive))
        return [[float(len(current))] for current in texts], len(texts)
