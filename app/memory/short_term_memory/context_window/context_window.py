from app.messages.message_base.message_base import MessageBase
from app.memory.short_term_memory.short_term_memory import ShortTermMemory
from app.memory.short_term_memory.context_window.context_window_operation.context_window_policy import ContextWindowPolicy
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_manager import ContextWindowOperationManager


class ContextWindow:
    """Bounded, policy-driven view over a Memory instance that produces the
    message list sent to the model on every inference call. The window never
    stores messages itself — Memory remains the single source of truth. When
    the number of messages reaches max_window_size, the injected policy resolves
    the operation pipeline and the manager executes it, yielding a transformed
    list that fits within the limit. Callers trigger a refresh via update() after
    each new message is appended to Memory; build() then returns the current view."""

    def __init__(self, memory: ShortTermMemory, max_window_size: int, policy: ContextWindowPolicy) -> None:
        self._memory: ShortTermMemory = memory
        self._max_window_size: int = max_window_size
        self._policy: ContextWindowPolicy = policy
        self._operation_manager: ContextWindowOperationManager = ContextWindowOperationManager()
        self._buffer: list[MessageBase] = []

    def update(self) -> None:
        messages = self._memory.get_all()
        if len(self._memory) >= self._max_window_size:
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
