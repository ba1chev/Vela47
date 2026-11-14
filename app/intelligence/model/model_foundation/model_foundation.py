from time import perf_counter
from typing import Iterator, Optional

from app.intelligence.model import ModelBase
from app.intelligence.model import ModelConfig
from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageBase
from app.intelligence.model import ModelClientBase
from app.intelligence.tracing import TraceEventType
from app.intelligence.model import ModelClientOllama
from app.intelligence.tracing import TracingServiceNull
from app.intelligence.tracing import TracingServiceBase


class ModelFoundation(ModelBase):
    """Text-generation model configured entirely by an injected ModelConfig and served
    by an injected ModelClientBase, a local Ollama server unless told otherwise.
    invoke() blocks for the full reply with its usage, stream() yields text as it is
    produced.

    Every call is reported to the tracer here, whatever the backend, so a run's token
    accounting comes from one place and reads the same in development and production.
    How messages, tools and an output schema reach a provider is the client's concern
    (see ModelClientOllama and ModelClientBedrock)."""

    def __init__(self, config: ModelConfig,
        tracing_service: Optional[TracingServiceBase] = None,
        client: Optional[ModelClientBase] = None) -> None:
        self._config = config
        self._tracing_service: TracingServiceBase = (
            tracing_service
            if tracing_service is not None
            else TracingServiceNull()
        )
        self._client: ModelClientBase = client if client is not None else ModelClientOllama()

    def _report(self, started: float, input_tokens: int, output_tokens: int, payload: dict) -> None:
        self._tracing_service.emit(
            TraceEventType.MODEL_INVOKED,
            self._config.model_name,
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                **payload
            },
            (perf_counter() - started) * 1000.0
        )

    def invoke(self, messages: list[MessageBase], tools: Optional[list[dict]] = None,
        output_schema: Optional[dict] = None) -> MessageAI:
        started = perf_counter()
        response = self._client.chat(self._config, messages, tools, output_schema)
        usage = response.usage_metadata
        self._report(
            started,
            usage.input_tokens if usage is not None else 0,
            usage.output_tokens if usage is not None else 0,
            {"tool_calls": [current_call.name for current_call in response.tool_calls], "messages": len(messages)}
        )
        return response

    def stream(self, messages: list[MessageBase]) -> Iterator[str]:
        started = perf_counter()
        input_tokens = 0
        output_tokens = 0
        for current_piece in self._client.stream(self._config, messages):
            if current_piece.usage_metadata is not None:
                input_tokens = current_piece.usage_metadata.input_tokens
                output_tokens = current_piece.usage_metadata.output_tokens
            content = current_piece.content if isinstance(current_piece.content, str) else str(current_piece.content)
            if content:
                yield content
        self._report(
            started, input_tokens, output_tokens,
            {"tool_calls": [], "messages": len(messages), "streamed": True}
        )
