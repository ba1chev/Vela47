from time import perf_counter
from typing import Any, Iterator, Optional

from app.intelligence.model import ModelBase
from app.intelligence.model import ModelConfig
from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageBase
from app.intelligence.model import ModelClientBase
from app.intelligence.tracing import TraceEventType
from app.intelligence.model import ModelClientOllama
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.tracing import current_tracing_service


class ModelFoundation(ModelBase):
    """Text-generation model configured entirely by an injected ModelConfig and served
    by an injected ModelClientBase, a local Ollama server unless told otherwise.
    invoke() blocks for the full reply with its usage, stream() yields text as it is
    produced.

    Every call is reported here, to the injected tracer or else to the run using the
    model (see current_tracing_service), whatever the backend, so a run's token
    accounting comes from one place and reads the same in development and production.
    How messages, tools and an output schema reach a provider is the client's concern
    (see ModelClientOllama and ModelClientBedrock)."""

    def __init__(self, config: ModelConfig,
        tracing_service: Optional[TracingServiceBase] = None,
        client: Optional[ModelClientBase] = None) -> None:
        self._config = config
        self._tracing_service: Optional[TracingServiceBase] = tracing_service
        self._client: ModelClientBase = client if client is not None else ModelClientOllama()

    def _tracer(self) -> TracingServiceBase:
        return self._tracing_service if self._tracing_service is not None else current_tracing_service()

    def _describe(self, message: MessageBase) -> dict[str, Any]:
        described: dict[str, Any] = {
            "role": message.type.value,
            "content": message.content if isinstance(message.content, str) else str(message.content)
        }
        if message.name:
            described["name"] = message.name
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            described["tool_calls"] = [{"name": current.name, "args": current.args} for current in tool_calls]
        if getattr(message, "tool_call_id", None):
            described["tool_call_id"] = message.tool_call_id
        return described

    def _request(self, messages: list[MessageBase], tools: Optional[list[dict]] = None,
        output_schema: Optional[dict] = None) -> dict[str, Any]:
        return {
            "backend": self._client.client_type.value,
            "config": self._config.model_dump(mode = "json", exclude = {"model_name"}, exclude_none = True),
            "messages": len(messages),
            "prompt": [self._describe(current_message) for current_message in messages],
            "tools": [current.get("function", {}).get("name", "") for current in tools or []],
            "output_schema": (output_schema or {}).get("title") if output_schema is not None else None
        }

    def _report(self, started: float, input_tokens: int, output_tokens: int, payload: dict[str, Any]) -> None:
        duration_ms = (perf_counter() - started) * 1000.0
        self._tracer().emit(
            TraceEventType.MODEL_INVOKED,
            self._config.model_name,
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "tokens_per_second": round(output_tokens / (duration_ms / 1000.0), 1) if duration_ms and output_tokens else None,
                **payload
            },
            duration_ms
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
            {
                **self._request(messages, tools, output_schema),
                "tool_calls": [current_call.name for current_call in response.tool_calls],
                "calls": [
                    {"name": current_call.name, "args": current_call.args, "id": current_call.id}
                    for current_call in response.tool_calls
                ],
                "response": response.content if isinstance(response.content, str) else str(response.content),
                **response.response_metadata.get("provider", {})
            }
        )
        return response

    def stream(self, messages: list[MessageBase]) -> Iterator[str]:
        started = perf_counter()
        first_token_ms: Optional[float] = None
        input_tokens = 0
        output_tokens = 0
        parts: list[str] = []
        provider: dict[str, Any] = {}
        for current_piece in self._client.stream(self._config, messages):
            if current_piece.usage_metadata is not None:
                input_tokens = current_piece.usage_metadata.input_tokens
                output_tokens = current_piece.usage_metadata.output_tokens
            provider = current_piece.response_metadata.get("provider", provider)
            content = current_piece.content if isinstance(current_piece.content, str) else str(current_piece.content)
            if content:
                if first_token_ms is None:
                    first_token_ms = round((perf_counter() - started) * 1000.0, 1)
                parts.append(content)
                yield content
        self._report(
            started, input_tokens, output_tokens,
            {
                **self._request(messages),
                "tool_calls": [],
                "streamed": True,
                "chunks": len(parts),
                "first_token_ms": first_token_ms,
                "response": "".join(parts),
                **provider
            }
        )
