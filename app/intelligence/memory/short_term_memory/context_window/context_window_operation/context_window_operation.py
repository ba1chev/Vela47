from abc import ABC, abstractmethod

from app.intelligence.messages import MessageBase
from app.intelligence.memory import ContextWindowOperationType


class ContextWindowOperation(ABC):
    """Abstract base for every transformation that can be applied to a context
    window's message list. Each concrete subclass implements one operation type —
    expand, shrink, slide, summarize, truncate, or flatten — and encapsulates
    its parameters at construction time. apply() is a pure function: it receives
    the current message list and returns a transformed one, never reading from or
    writing to Memory directly."""

    @property
    @abstractmethod
    def operation_type(self) -> ContextWindowOperationType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def apply(self, messages: list[MessageBase]) -> list[MessageBase]:
        raise NotImplementedError("Must be implemented")
