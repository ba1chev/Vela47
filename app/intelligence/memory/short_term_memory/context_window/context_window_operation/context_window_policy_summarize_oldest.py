from typing import Callable

from app.intelligence.messages.message_base.message_base import MessageBase
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_policy import ContextWindowPolicy
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation import ContextWindowOperation
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation_summarize import ContextWindowOperationSummarize


class SummarizeOldestPolicy(ContextWindowPolicy):
    """Compresses the `n` oldest messages into a single MessageSystem summary
    whenever the window reaches capacity. Frees `n - 1` slots while preserving
    the semantic content of evicted turns — unlike SlidingWindowPolicy, which
    discards them entirely. Requires a summarizer callable that accepts a message
    list and returns a summary string; this is intentionally decoupled so callers
    can supply a second model call, a simple text join, or any other strategy.
    Supply both parameters at construction time:
    SummarizeOldestPolicy(n=4, summarizer=my_fn)."""

    def __init__(self, n: int, summarizer: Callable[[list[MessageBase]], str]) -> None:
        self._n = n
        self._summarizer = summarizer

    def resolve(self, messages: list[MessageBase],
        capacity: int) -> list[ContextWindowOperation]:
        return [ContextWindowOperationSummarize(n = self._n, summarizer = self._summarizer)]
