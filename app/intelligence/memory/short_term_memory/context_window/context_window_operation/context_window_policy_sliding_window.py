from app.intelligence.messages import MessageBase
from app.intelligence.memory import ContextWindowPolicy
from app.intelligence.memory import ContextWindowOperation
from app.intelligence.memory import ContextWindowOperationSlide


class SlidingWindowPolicy(ContextWindowPolicy):
    """Advances the context window by dropping the `step` oldest messages every
    time the window reaches capacity. Simple, predictable, and zero-overhead —
    no model call required. Best for sessions where recency dominates and losing
    the earliest turns is acceptable. Supply the step at construction time;
    defaults to 2 so one full exchange (human + AI) is evicted per overflow."""

    def __init__(self, step: int = 2) -> None:
        self._step = step

    def resolve(self, messages: list[MessageBase],
        capacity: int) -> list[ContextWindowOperation]:
        return [ContextWindowOperationSlide(step = self._step)]
