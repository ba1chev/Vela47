from app.intelligence.messages.message_base.message_base import MessageBase
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation import ContextWindowOperation


class ContextWindowOperationManager:
    """Executes an ordered pipeline of ContextWindowOperation instances against
    a message list. Each operation receives the output of the previous one,
    forming a composable transformation chain. The manager owns no state beyond
    the pipeline — it never reads from or writes to Memory directly, and the
    same instance can safely process multiple independent pipelines."""

    def apply(self, operations: list[ContextWindowOperation],
        messages: list[MessageBase]) -> list[MessageBase]:
        result = messages
        for operation in operations:
            result = operation.apply(result)
        return result
