import ollama
from uuid import uuid4
from typing import Iterator, Optional

from app.intelligence.model import ModelConfig
from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageTool
from app.intelligence.messages import MessageBase
from app.intelligence.model import MODEL_ROLE_MAP
from app.intelligence.model import ModelClientType
from app.intelligence.model import ModelClientBase
from app.intelligence.messages import MessageToolCall
from app.intelligence.messages import MessageUsageMetadata


class ModelClientOllama(ModelClientBase):
    """A local Ollama server, reached through the ollama package and OLLAMA_HOST.
    Assistant turns are sent with their tool calls and tool results with their tool's
    name, so the model can pair each result with its call.

    think is passed as its own Ollama parameter, because inside options it is ignored
    and the model reasons on every call. An output_schema is passed as format and
    constrains decoding to matching JSON, which a schema described in the prompt cannot
    do for a small model. The context size goes in as num_ctx."""

    @property
    def client_type(self) -> ModelClientType:
        return ModelClientType.OLLAMA

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

    def _build_options(self, config: ModelConfig) -> dict:
        options: dict = {
            "temperature": config.temperature,
            "top_p": config.top_p,
            "top_k": config.top_k,
            "repeat_penalty": config.repeat_penalty
        }
        if config.seed is not None:
            options["seed"] = config.seed
        if config.stop is not None:
            options["stop"] = config.stop
        if config.context_window_tokens is not None:
            options["num_ctx"] = config.context_window_tokens
        if config.max_output_tokens is not None:
            options["num_predict"] = config.max_output_tokens
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

    def _usage(self, input_tokens: int, output_tokens: int) -> MessageUsageMetadata:
        return MessageUsageMetadata(
            input_tokens = input_tokens,
            output_tokens = output_tokens,
            total_tokens = input_tokens + output_tokens
        )

    def chat(self, config: ModelConfig, messages: list[MessageBase], tools: Optional[list[dict]] = None,
        output_schema: Optional[dict] = None) -> MessageAI:
        response = ollama.chat(
            model = config.model_name,
            messages = self._format_messages(messages),
            options = self._build_options(config),
            keep_alive = config.keep_alive,
            tools = tools,
            think = config.think,
            format = output_schema
        )
        return MessageAI(
            content = response["message"]["content"],
            tool_calls = self._parse_tool_calls(response["message"]),
            usage_metadata = self._usage(
                response.get("prompt_eval_count", 0) or 0, response.get("eval_count", 0) or 0
            )
        )

    def stream(self, config: ModelConfig, messages: list[MessageBase]) -> Iterator[MessageAI]:
        input_tokens = 0
        output_tokens = 0
        for chunk in ollama.chat(
            model = config.model_name,
            messages = self._format_messages(messages),
            options = self._build_options(config),
            keep_alive = config.keep_alive,
            stream = True,
            think = config.think
        ):
            input_tokens = chunk.get("prompt_eval_count", 0) or input_tokens
            output_tokens = chunk.get("eval_count", 0) or output_tokens
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield MessageAI(content = content)
        yield MessageAI(content = "", usage_metadata = self._usage(input_tokens, output_tokens))

    def embed(self, model_name: str, texts: list[str], keep_alive: str) -> tuple[list[list[float]], int]:
        response = ollama.embed(model = model_name, input = texts, keep_alive = keep_alive)
        vectors = [list(current_vector) for current_vector in response["embeddings"]]
        return vectors, response.get("prompt_eval_count", 0) or 0
