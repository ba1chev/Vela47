from typing import Optional

from app.intelligence.messages.message_base.message_base import MessageBase
from app.intelligence.memory.short_term_memory.short_term_memory import ShortTermMemory
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_policy import ContextWindowPolicy
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation_manager import ContextWindowOperationManager


class ContextWindow:
    """Bounded, policy-driven view over a Memory instance that produces the
    message list sent to the model on every inference call. The window never
    stores messages itself — Memory remains the single source of truth. The
    policy is not fixed at construction — middleware injects it via set_policy()
    before each update() call. When the number of messages reaches max_window_size
    and no policy has been set, update() raises RuntimeError. Callers trigger a
    refresh via update() after each new message is appended to Memory; build()
    then returns the current view."""

    def __init__(self, memory: ShortTermMemory, max_window_size: int) -> None:
        self._memory: ShortTermMemory = memory
        self._max_window_size: int = max_window_size
        self._policy: Optional[ContextWindowPolicy] = None
        self._operation_manager: ContextWindowOperationManager = ContextWindowOperationManager()
        self._buffer: list[MessageBase] = []

    def set_policy(self, policy: ContextWindowPolicy) -> None:
        self._policy = policy

    def update(self) -> None:
        messages = self._memory.get_all()
        if len(self._memory) >= self._max_window_size:
            if self._policy is None:
                raise RuntimeError(
                    "ContextWindow reached capacity but no policy is set. "
                    "Inject a policy via set_policy() before calling update()."
                )
            operations = self._policy.resolve(messages, self._max_window_size)
            messages = self._operation_manager.apply(operations, messages)
        self._buffer = messages

    def build(self) -> list[MessageBase]:
        return self._buffer

    def size(self) -> int:
        return len(self._buffer)

    def is_full(self) -> bool:
        return len(self._memory) >= self._max_window_size

    def is_empty(self) -> bool:
        return len(self._memory) == 0

    def fits(self, message: MessageBase) -> bool:
        return len(self._memory) + 1 <= self._max_window_size
