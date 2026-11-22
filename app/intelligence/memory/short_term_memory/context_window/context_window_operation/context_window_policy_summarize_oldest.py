from typing import Callable

from app.intelligence.messages import MessageBase
from app.intelligence.memory import ContextWindowPolicy
from app.intelligence.memory import ContextWindowOperation
from app.intelligence.memory import ContextWindowOperationSummarize


class SummarizeOldestPolicy(ContextWindowPolicy):
    """Compresses the oldest messages into a single MessageSystem summary whenever the
    window reaches capacity: the `n` oldest at capacity, plus one for every message the
    memory has grown past it, so the window always comes back to capacity - n + 1. It
    preserves the semantic content of evicted turns, unlike SlidingWindowPolicy, which
    discards them entirely. The summarizer is any callable that accepts a message list
    and returns a summary string — a second model call, a simple text join or anything
    else: SummarizeOldestPolicy(n=4, summarizer=my_fn)."""

    def __init__(self, n: int, summarizer: Callable[[list[MessageBase]], str]) -> None:
        self._n = n
        self._summarizer = summarizer

    def resolve(self, messages: list[MessageBase],
        capacity: int) -> list[ContextWindowOperation]:
        count = max(self._n, len(messages) - capacity + self._n)
        return [ContextWindowOperationSummarize(n = count, summarizer = self._summarizer)]
