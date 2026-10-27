from typing import Iterator
from abc import ABC, abstractmethod

from app.messages.message_ai import MessageAI
from app.messages.message_base.message_base import MessageBase


class ModelBase(ABC):
    """Abstract base for every model implementation in the framework. Defines
    the two core inference modes — invoke for a single blocking response and
    stream for a token-by-token generator — so agents and pipelines can depend
    on this interface rather than a concrete provider. Concrete subclasses wire
    up a specific backend (e.g. Ollama) and translate between MessageBase and
    the provider's native format."""

    @abstractmethod
    def invoke(self, messages: list[MessageBase]) -> MessageAI:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def stream(self, messages: list[MessageBase]) -> Iterator[str]:
        raise NotImplementedError("Must be implemented")
