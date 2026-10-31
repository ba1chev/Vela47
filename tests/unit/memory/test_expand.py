from app.intelligence.messages import MessageHuman
from app.intelligence.memory import ContextWindowOperationType
from app.intelligence.memory import ContextWindowOperationExpand


def make_messages(*contents):
    return [MessageHuman(content = c) for c in contents]


class TestExpand:
    def test_returns_same_list(self):
        msgs = make_messages("a", "b", "c")
        result = ContextWindowOperationExpand().apply(msgs)
        assert result == msgs

    def test_empty_list(self):
        assert ContextWindowOperationExpand().apply([]) == []

    def test_operation_type(self):
        assert ContextWindowOperationExpand().operation_type == ContextWindowOperationType.EXPAND
