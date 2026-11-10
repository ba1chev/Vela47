import ollama
from uuid import uuid4
from time import perf_counter
from typing import Iterator, Optional

from app.intelligence.model import ModelBase
from app.intelligence.model import ModelConfig
from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageTool
from app.intelligence.messages import MessageBase
from app.intelligence.model import MODEL_ROLE_MAP
from app.intelligence.tracing import TraceEventType
from app.intelligence.messages import MessageToolCall
from app.intelligence.tracing import TracingServiceNull
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.messages import MessageUsageMetadata


class ModelFoundation(ModelBase):
    """Text-generation model backed by a local Ollama server, configured entirely by an
    injected ModelConfig. invoke() blocks for the full reply with its usage, stream()
    yields text as it is produced, and every invoke() is reported to the tracer, the
    only place a run's token accounting comes from.

    Assistant turns are sent with their tool calls and tool results with their tool's
    name, so the model can pair each result with its call. think is passed as its own
    Ollama parameter, because inside options it is ignored and the model reasons on
    every call. An output_schema is passed as format and constrains decoding to matching
    JSON, which a schema described in the prompt cannot do for a small model."""

    def __init__(self, config: ModelConfig,
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        self._config = config
        self._tracing_service: TracingServiceBase = (
            tracing_service
            if tracing_service is not None
            else TracingServiceNull()
        )

    def _format_message(self, message: MessageBase) -> dict:
        formatted: dict = {
            "role": MODEL_ROLE_MAP[message.type],
            "content": message.content if isinstance(message.content, str) else str(message.content)
        }
        if isinstance(message, MessageAI) and message.tool_calls:
            formatted["tool_calls"] = [
                {"function": {"name": current_call.name, "arguments": current_call.args}}
                for current_call in message.tool_calls
            ]
        if isinstance(message, MessageTool) and message.name:
            formatted["tool_name"] = message.name
        return formatted

    def _format_messages(self, messages: list[MessageBase]) -> list[dict]:
        return [self._format_message(current_message) for current_message in messages]

    def _build_options(self) -> dict:
        options: dict = {
            "temperature": self._config.temperature,
            "top_p": self._config.top_p,
            "top_k": self._config.top_k,
            "repeat_penalty": self._config.repeat_penalty
        }
        if self._config.seed is not None:
            options["seed"] = self._config.seed
        if self._config.stop is not None:
            options["stop"] = self._config.stop
        if self._config.context_window_tokens is not None:
            options["num_ctx"] = self._config.context_window_tokens
        if self._config.max_output_tokens is not None:
            options["num_predict"] = self._config.max_output_tokens
        return options

    def _parse_tool_calls(self, message: dict) -> list[MessageToolCall]:
        return [
            MessageToolCall(
                name = current_call["function"]["name"],
                args = current_call["function"].get("arguments", {}) or {},
                id = str(uuid4())
            )
            for current_call in (message.get("tool_calls") or [])
        ]

    def invoke(self, messages: list[MessageBase], tools: Optional[list[dict]] = None,
        output_schema: Optional[dict] = None) -> MessageAI:
        start = perf_counter()
        response = ollama.chat(
            model = self._config.model_name,
            messages = self._format_messages(messages),
            options = self._build_options(),
            keep_alive = self._config.keep_alive,
            tools = tools,
            think = self._config.think,
            format = output_schema
        )
        input_tokens = response.get("prompt_eval_count", 0)
        output_tokens = response.get("eval_count", 0)
        tool_calls = self._parse_tool_calls(response["message"])

        self._tracing_service.emit(
            TraceEventType.MODEL_INVOKED,
            self._config.model_name,
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "tool_calls": [current_call.name for current_call in tool_calls],
                "messages": len(messages)
            },
            (perf_counter() - start) * 1000.0
        )

        return MessageAI(
            content = response["message"]["content"],
            tool_calls = tool_calls,
            usage_metadata = MessageUsageMetadata(
                input_tokens = input_tokens,
                output_tokens = output_tokens,
                total_tokens = input_tokens + output_tokens
            )
        )

    def stream(self, messages: list[MessageBase]) -> Iterator[str]:
        start = perf_counter()
        input_tokens = 0
        output_tokens = 0

        for chunk in ollama.chat(
            model = self._config.model_name,
            messages = self._format_messages(messages),
            options = self._build_options(),
            keep_alive = self._config.keep_alive,
            stream = True,
            think = self._config.think
        ):
            input_tokens = chunk.get("prompt_eval_count", 0) or input_tokens
            output_tokens = chunk.get("eval_count", 0) or output_tokens
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content

        self._tracing_service.emit(
            TraceEventType.MODEL_INVOKED,
            self._config.model_name,
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "tool_calls": [],
                "messages": len(messages),
                "streamed": True
            },
            (perf_counter() - start) * 1000.0
        )
