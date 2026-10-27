import ollama
from typing import Iterator

from app.model.mode_base import ModelBase
from app.messages.message_ai import MessageAI
from app.model.model_config import ModelConfig
from app.messages.message_base.message_base import MessageBase
from app.model.model_foundation.model_role_map import MODEL_ROLE_MAP
from app.messages.message_usage_metadata import MessageUsageMetadata


class ModelFoundation(ModelBase):
    """Concrete text-generation model backed by a local Ollama server. All
    sampling behaviour is driven by an injected ModelConfig — no hard-coded
    defaults live here. _format_messages() translates the framework's MessageBase
    list into Ollama's role/content dict format using _ROLE_MAP. invoke() blocks
    until the full response arrives and attaches a populated MessageUsageMetadata;
    stream() yields raw text chunks as they are produced, token by token."""

    def __init__(self, config: ModelConfig) -> None:
        self._config = config

    def _format_messages(self, messages: list[MessageBase]) -> list[dict]:
        return [
            {
                "role": MODEL_ROLE_MAP[current_message.type],
                "content": current_message.content 
                if isinstance(current_message.content, str) 
                else str(current_message.content)
            }
            for current_message in messages
        ]

    def _build_options(self) -> dict:
        options: dict = {
            "temperature": self._config.temperature,
            "top_p": self._config.top_p,
            "top_k": self._config.top_k,
            "repeat_penalty": self._config.repeat_penalty,
            "think": self._config.think
        }
        if self._config.seed is not None:
            options["seed"] = self._config.seed
        if self._config.stop is not None:
            options["stop"] = self._config.stop
        if self._config.max_output_tokens is not None:
            options["num_predict"] = self._config.max_output_tokens
        return options

    def invoke(self, messages: list[MessageBase]) -> MessageAI:
        response = ollama.chat(
            model = self._config.model_name,
            messages = self._format_messages(messages),
            options = self._build_options(),
            keep_alive = self._config.keep_alive
        )
        input_tokens = response.get("prompt_eval_count", 0)
        output_tokens = response.get("eval_count", 0)
        return MessageAI(
            content = response["message"]["content"],
            usage_metadata = MessageUsageMetadata(
                input_tokens = input_tokens,
                output_tokens = output_tokens,
                total_tokens = input_tokens + output_tokens
            )
        )

    def stream(self, messages: list[MessageBase]) -> Iterator[str]:
        for chunk in ollama.chat(
            model = self._config.model_name,
            messages = self._format_messages(messages),
            options = self._build_options(),
            keep_alive = self._config.keep_alive,
            stream = True
        ):
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
