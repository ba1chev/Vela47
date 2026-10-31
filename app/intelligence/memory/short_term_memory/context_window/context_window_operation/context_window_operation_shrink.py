from app.intelligence.messages import MessageBase
from app.intelligence.memory import ContextWindowOperation
from app.intelligence.memory import ContextWindowOperationType


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
