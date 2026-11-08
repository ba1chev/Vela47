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
    """Concrete text-generation model backed by a local Ollama server. All
    sampling behaviour is driven by an injected ModelConfig — no hard-coded
    defaults live here. _format_messages() translates the framework's MessageBase
    list into Ollama's role/content dict format using _ROLE_MAP. invoke() blocks
    until the full response arrives and attaches a populated MessageUsageMetadata;
    stream() yields raw text chunks as they are produced, token by token.

    An assistant turn that called tools is sent with those calls, and a tool result with
    the name of the tool that produced it. Without them a model reading its own history
    sees results to requests it has no record of making, and with more than one tool it
    cannot tell which result answers which call.

    think is handed to Ollama as a parameter of its own, not among the sampling
    options. Ollama ignores it there, and a reasoning model then thinks on every call
    whatever the config says — dozens of times slower for a one-line reply, with the
    reasoning sometimes leaking into the answer.

    An output_schema is handed to Ollama as format, which constrains decoding to JSON
    that matches it. Describing a schema in the prompt is not enough for a small model:
    asked for a plan, qwen3:1.7b answers some goals with the schema itself, every time,
    and that reply can never be parsed. Constrained, it cannot produce anything else.

    Every invoke() is reported to the injected tracer, which is where a run's token
    accounting comes from — the model is the only component that sees usage, so if
    it stays silent no layer above it can report cost."""

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
