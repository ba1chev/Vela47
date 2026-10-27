from app.messages.message_base.message_base import MessageBase
from app.memory.short_term_memory.context_window.context_window_operation.context_window_policy import ContextWindowPolicy
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation import ContextWindowOperation
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_slide import ContextWindowOperationSlide


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
