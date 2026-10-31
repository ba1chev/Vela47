from app.intelligence.messages.message_base.message_base import MessageBase
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation import ContextWindowOperation
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType


class ContextWindowOperationSlide(ContextWindowOperation):
    """Advances the window forward by dropping the `step` oldest messages and
    keeping everything after them. Preserves the full content of retained
    messages unlike SHRINK, which hard-caps the list length. Use this in
    rolling-window policies where recency matters but the drop amount should be
    predictable and small — e.g. drop one pair of turns at a time. Defaults to
    a step of 1 if not supplied."""

    def __init__(self, step: int = 1) -> None:
        self._step = step

    @property
    def operation_type(self) -> ContextWindowOperationType:
        return ContextWindowOperationType.SLIDE

    def apply(self, messages: list[MessageBase]) -> list[MessageBase]:
        return messages[self._step:]
