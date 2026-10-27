from app.messages.message_human import MessageHuman
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_shrink import ContextWindowOperationShrink


def make_messages(*contents):
    return [MessageHuman(content = c) for c in contents]


class TestShrink:
    def test_keeps_last_n(self):
        msgs = make_messages("a", "b", "c", "d", "e")
        result = ContextWindowOperationShrink(n = 3).apply(msgs)
        assert len(result) == 3
        assert result[0].content == "c"

    def test_no_op_when_shorter_than_n(self):
        msgs = make_messages("a", "b")
        result = ContextWindowOperationShrink(n = 5).apply(msgs)
        assert len(result) == 2

    def test_exact_size(self):
        msgs = make_messages("a", "b", "c")
        result = ContextWindowOperationShrink(n = 3).apply(msgs)
        assert len(result) == 3

    def test_n_equals_one(self):
        msgs = make_messages("a", "b", "c")
        result = ContextWindowOperationShrink(n = 1).apply(msgs)
        assert len(result) == 1
        assert result[0].content == "c"

    def test_operation_type(self):
        assert ContextWindowOperationShrink(n = 1).operation_type == ContextWindowOperationType.SHRINK
