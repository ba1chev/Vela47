from math import ceil

from app.intelligence.messages import MessageBase
from app.intelligence.memory import ContextWindowPolicy
from app.intelligence.memory import ContextWindowOperation
from app.intelligence.memory import ContextWindowOperationSlide


class SlidingWindowPolicy(ContextWindowPolicy):
    """Advances the context window by dropping the oldest messages in multiples of
    `step` every time the window reaches capacity. Simple, predictable, and
    zero-overhead — no model call required. Best for sessions where recency dominates
    and losing the earliest turns is acceptable. Defaults to a step of 2, so one full
    exchange (human + AI) is evicted per overflow.

    The window is rebuilt from the whole memory on every update, so the policy drops as
    many steps as the memory has outgrown the capacity: the window stays below it
    instead of growing with every turn after the first overflow."""

    def __init__(self, step: int = 2) -> None:
        self._step = step

    def resolve(self, messages: list[MessageBase],
        capacity: int) -> list[ContextWindowOperation]:
        steps = max(1, ceil((len(messages) - capacity + 1) / self._step))
        return [ContextWindowOperationSlide(step = self._step * steps)]
