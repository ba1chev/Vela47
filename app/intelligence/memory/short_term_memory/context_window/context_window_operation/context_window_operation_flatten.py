from app.intelligence.messages.message_base.message_base import MessageBase
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation import ContextWindowOperation
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType


class ContextWindowOperationFlatten(ContextWindowOperation):
    """Merges consecutive messages of the same role into a single message by
    joining their content with a newline. Reduces the total message count
    without discarding any text — useful after TRUNCATE or as a pre-processing
    step before sending to a model that charges per-message overhead. Produces
    new frozen message instances via model_copy so Memory is never mutated.
    Non-consecutive runs of the same role are kept separate."""

    @property
    def operation_type(self) -> ContextWindowOperationType:
        return ContextWindowOperationType.FLATTEN

    def apply(self, messages: list[MessageBase]) -> list[MessageBase]:
        if not messages:
            return []

        result = []
        current = messages[0]

        for msg in messages[1:]:
            if msg.type == current.type:
                current_content = (
                    current.content if isinstance(current.content, str) else str(current.content)
                )
                msg_content = (
                    msg.content if isinstance(msg.content, str) else str(msg.content)
                )
                current = current.model_copy(update = {"content": current_content + "\n" + msg_content})
            else:
                result.append(current)
                current = msg

        result.append(current)
        return result
