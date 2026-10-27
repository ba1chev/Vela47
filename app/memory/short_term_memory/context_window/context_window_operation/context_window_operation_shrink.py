from app.messages.message_base.message_base import MessageBase
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation import ContextWindowOperation
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType


class ContextWindowOperationShrink(ContextWindowOperation):
    """Keeps only the `n` most recent messages, dropping every older entry.
    Use this when the priority is recency — the model sees the latest context
    but loses earlier turns entirely. Supply `n` at construction time:
    ContextWindowOperationShrink(n=10). If the list is already shorter than `n`
    it is returned unchanged."""

    def __init__(self, n: int) -> None:
        self._n = n

    @property
    def operation_type(self) -> ContextWindowOperationType:
        return ContextWindowOperationType.SHRINK

    def apply(self, messages: list[MessageBase]) -> list[MessageBase]:
        return messages[-self._n:] if len(messages) > self._n else messages
