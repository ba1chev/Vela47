from app.messages.message_base.message_base import MessageBase
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation import ContextWindowOperation
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType


class ContextWindowOperationTruncate(ContextWindowOperation):
    """Trims the content of every message to at most `max_chars` characters.
    Produces new frozen message instances via model_copy so the originals in
    Memory are never mutated. Use this to reduce prompt token consumption
    when individual messages are long but all turns must be retained — as a
    composable step before SLIDE or SHRINK, or as a standalone policy action.
    Supply the character limit at construction time:
    ContextWindowOperationTruncate(max_chars=512)."""

    def __init__(self, max_chars: int) -> None:
        self._max_chars = max_chars

    @property
    def operation_type(self) -> ContextWindowOperationType:
        return ContextWindowOperationType.TRUNCATE

    def apply(self, messages: list[MessageBase]) -> list[MessageBase]:
        result = []
        for msg in messages:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            if len(content) > self._max_chars:
                content = content[:self._max_chars]
            result.append(msg.model_copy(update = {"content": content}))
        return result
