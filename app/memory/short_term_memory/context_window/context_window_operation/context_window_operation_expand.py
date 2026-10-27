from app.messages.message_base.message_base import MessageBase
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation import ContextWindowOperation
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType


class ContextWindowOperationExpand(ContextWindowOperation):
    """Returns the message list unchanged, signalling that the window may grow
    beyond its nominal capacity without any eviction. Use this as the terminal
    operation in a policy that prefers keeping all context over compressing it —
    for example when total message count is still manageable and the cost of
    losing context outweighs the overhead of a larger prompt."""

    @property
    def operation_type(self) -> ContextWindowOperationType:
        return ContextWindowOperationType.EXPAND

    def apply(self, messages: list[MessageBase]) -> list[MessageBase]:
        return messages
