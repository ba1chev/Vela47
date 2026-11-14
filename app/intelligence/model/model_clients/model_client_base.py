from abc import ABC, abstractmethod
from typing import Iterator, Optional

from app.intelligence.model import ModelConfig
from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageBase
from app.intelligence.model import ModelClientType


class ModelClientBase(ABC):
    """Abstract base for the backend a model is served by. It translates the
    framework's messages, tools and output schema into one provider's request and its
    reply back into a MessageAI with its token usage, and nothing else: tracing, and
    which model with which sampling, stay with ModelFoundation and ModelEmbeddings, so
    every backend is accounted for the same way.

    stream() yields the reply as MessageAI pieces, and the last one carries the usage
    and no text. embed() returns the vectors in the order of the texts, with the input
    tokens they cost."""

    @property
    @abstractmethod
    def client_type(self) -> ModelClientType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def chat(self, config: ModelConfig, messages: list[MessageBase], tools: Optional[list[dict]] = None,
        output_schema: Optional[dict] = None) -> MessageAI:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def stream(self, config: ModelConfig, messages: list[MessageBase]) -> Iterator[MessageAI]:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def embed(self, model_name: str, texts: list[str], keep_alive: str) -> tuple[list[list[float]], int]:
        raise NotImplementedError("Must be implemented")
