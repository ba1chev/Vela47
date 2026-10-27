from app.messages.message_ai import MessageAI
from app.messages.message_human import MessageHuman
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_truncate import ContextWindowOperationTruncate


class TestTruncate:
    def test_truncates_long_content(self):
        msgs = [MessageHuman(content = "hello world")]
        result = ContextWindowOperationTruncate(max_chars = 5).apply(msgs)
        assert result[0].content == "hello"

    def test_no_truncate_if_short(self):
        msgs = [MessageHuman(content = "hi")]
        result = ContextWindowOperationTruncate(max_chars = 10).apply(msgs)
        assert result[0].content == "hi"

    def test_exact_length_unchanged(self):
        msgs = [MessageHuman(content = "hello")]
        result = ContextWindowOperationTruncate(max_chars = 5).apply(msgs)
        assert result[0].content == "hello"

    def test_original_not_mutated(self):
        original = MessageHuman(content = "long content here")
        result = ContextWindowOperationTruncate(max_chars = 4).apply([original])
        assert original.content == "long content here"
        assert result[0].content == "long"

    def test_multiple_messages(self):
        msgs = [MessageHuman(content = "abcde"), MessageAI(content = "fghij")]
        result = ContextWindowOperationTruncate(max_chars = 3).apply(msgs)
        assert result[0].content == "abc"
        assert result[1].content == "fgh"

    def test_operation_type(self):
        assert ContextWindowOperationTruncate(max_chars = 10).operation_type == ContextWindowOperationType.TRUNCATE
