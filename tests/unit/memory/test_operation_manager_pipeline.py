from app.messages.message_human import MessageHuman
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_flatten import ContextWindowOperationFlatten
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_manager import ContextWindowOperationManager
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_truncate import ContextWindowOperationTruncate


def make_messages(*contents):
    return [MessageHuman(content = c) for c in contents]


class TestOperationManagerPipeline:
    def test_chained_truncate_then_flatten(self):
        msgs = [MessageHuman(content = "hello world"), MessageHuman(content = "foo bar")]
        manager = ContextWindowOperationManager()
        result = manager.apply(
            [ContextWindowOperationTruncate(max_chars = 5), ContextWindowOperationFlatten()],
            msgs
        )
        assert len(result) == 1
        assert result[0].content == "hello\nfoo b"

    def test_empty_operations_returns_unchanged(self):
        msgs = make_messages("a", "b")
        result = ContextWindowOperationManager().apply([], msgs)
        assert result == msgs
