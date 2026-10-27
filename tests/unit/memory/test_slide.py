from app.messages.message_human import MessageHuman
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_slide import ContextWindowOperationSlide


def make_messages(*contents):
    return [MessageHuman(content = c) for c in contents]


class TestSlide:
    def test_drops_first_step(self):
        msgs = make_messages("a", "b", "c", "d")
        result = ContextWindowOperationSlide(step = 2).apply(msgs)
        assert len(result) == 2
        assert result[0].content == "c"

    def test_default_step_one(self):
        msgs = make_messages("a", "b", "c")
        result = ContextWindowOperationSlide().apply(msgs)
        assert len(result) == 2
        assert result[0].content == "b"

    def test_slide_entire_list(self):
        msgs = make_messages("a", "b")
        result = ContextWindowOperationSlide(step = 2).apply(msgs)
        assert result == []

    def test_operation_type(self):
        assert ContextWindowOperationSlide().operation_type == ContextWindowOperationType.SLIDE
