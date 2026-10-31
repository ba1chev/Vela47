from typing import Callable

from app.intelligence.middleware import MiddlewareBase
from app.intelligence.messages import MessageBase
from app.intelligence.memory import ContextWindow
from app.intelligence.memory import SummarizeOldestPolicy


class MiddlewareSummarization(MiddlewareBase[ContextWindow]):
    """Injects a SummarizeOldestPolicy into the ContextWindow before each update.
    When the window reaches capacity, the `n` oldest messages are compressed into
    a single MessageSystem summary produced by the supplied summarizer callable.
    The summarizer is intentionally decoupled — pass a second model call, a text
    join, or any function that accepts a message list and returns a string:
    MiddlewareSummarization(n=4, summarizer=my_fn)."""

    def __init__(self, n: int, summarizer: Callable[[list[MessageBase]], str]) -> None:
        self._policy = SummarizeOldestPolicy(n = n, summarizer = summarizer)

    def process(self, target: ContextWindow) -> None:
        target.set_policy(self._policy)
        target.update()
