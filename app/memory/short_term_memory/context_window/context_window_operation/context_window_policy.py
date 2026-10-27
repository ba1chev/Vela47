from abc import ABC, abstractmethod

from app.messages.message_base.message_base import MessageBase
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation import ContextWindowOperation


class ContextWindowPolicy(ABC):
    """Decides which sequence of ContextWindowOperation instances to apply when
    the window reaches capacity. Concrete subclasses encode a specific eviction
    strategy — slide the window, compress via summarisation, truncate individual
    messages, or any composition thereof. The policy is stateless: given the same
    message list and capacity it always produces the same operation pipeline,
    which the ContextWindowOperationManager then executes."""

    @abstractmethod
    def resolve(self, messages: list[MessageBase],
        capacity: int) -> list[ContextWindowOperation]:
        raise NotImplementedError("Must be implemented")
