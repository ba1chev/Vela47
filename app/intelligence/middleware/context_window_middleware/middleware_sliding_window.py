from app.intelligence.middleware.middleware_base import MiddlewareBase
from app.intelligence.memory.short_term_memory.context_window.context_window import ContextWindow
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_policy_sliding_window import SlidingWindowPolicy


class MiddlewareSlidingWindow(MiddlewareBase[ContextWindow]):
    """Injects a SlidingWindowPolicy into the ContextWindow before each update.
    When the window reaches capacity, the `step` oldest messages are dropped to
    make room for incoming ones. Zero-overhead — no model call required. Best
    for sessions where recency dominates and losing the earliest turns is
    acceptable. Supply the step at construction time; defaults to 2 so one full
    exchange (human + AI) is evicted per overflow:
    MiddlewareSlidingWindow(step=2)."""

    def __init__(self, step: int = 2) -> None:
        self._policy = SlidingWindowPolicy(step = step)

    def process(self, target: ContextWindow) -> None:
        target.set_policy(self._policy)
        target.update()
