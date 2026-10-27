from abc import ABC, abstractmethod

from app.messages.message_base.message_base import MessageBase
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType


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
