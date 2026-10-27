from app.messages.message_ai import MessageAI
from app.messages.message_human import MessageHuman
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_flatten import ContextWindowOperationFlatten


class TestFlatten:
    def test_merges_consecutive_same_role(self):
        msgs = [MessageHuman(content = "a"), MessageHuman(content = "b"), MessageAI(content = "c")]
        result = ContextWindowOperationFlatten().apply(msgs)
        assert len(result) == 2
        assert "a\nb" == result[0].content

    def test_no_merge_alternating(self):
        msgs = [MessageHuman(content = "a"), MessageAI(content = "b"), MessageHuman(content = "c")]
        result = ContextWindowOperationFlatten().apply(msgs)
        assert len(result) == 3

    def test_empty_list(self):
        assert ContextWindowOperationFlatten().apply([]) == []

    def test_single_message_unchanged(self):
        msgs = [MessageHuman(content = "only")]
        result = ContextWindowOperationFlatten().apply(msgs)
        assert len(result) == 1
        assert result[0].content == "only"

    def test_all_same_role_merged_into_one(self):
        msgs = [MessageHuman(content = "x"), MessageHuman(content = "y"), MessageHuman(content = "z")]
        result = ContextWindowOperationFlatten().apply(msgs)
        assert len(result) == 1
        assert result[0].content == "x\ny\nz"

    def test_operation_type(self):
        assert ContextWindowOperationFlatten().operation_type == ContextWindowOperationType.FLATTEN
