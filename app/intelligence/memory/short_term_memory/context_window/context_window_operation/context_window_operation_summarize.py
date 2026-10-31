from typing import Callable

from app.intelligence.messages.message_system import MessageSystem
from app.intelligence.messages.message_base.message_base import MessageBase
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation import ContextWindowOperation
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType


class ContextWindowOperationSummarize(ContextWindowOperation):
    """Compresses the first `n` messages into a single MessageSystem summary
    produced by a caller-supplied summarizer function, then appends the
    remaining messages unchanged. This preserves recency while replacing the
    oldest context with a compact representation rather than discarding it
    entirely. The summarizer is decoupled from any specific model — pass any
    callable that accepts a message list and returns a summary string:
    ContextWindowOperationSummarize(n=6, summarizer=my_fn)."""

    def __init__(self, n: int, summarizer: Callable[[list[MessageBase]], str]) -> None:
        self._n = n
        self._summarizer = summarizer

    @property
    def operation_type(self) -> ContextWindowOperationType:
        return ContextWindowOperationType.SUMMARIZE

    def apply(self, messages: list[MessageBase]) -> list[MessageBase]:
        to_compress = messages[:self._n]
        remainder = messages[self._n:]
        summary_text = self._summarizer(to_compress)
        summary = MessageSystem(content = summary_text)
        return [summary] + remainder
