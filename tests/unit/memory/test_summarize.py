from app.messages.message_human import MessageHuman
from app.messages.message_system import MessageSystem
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_summarize import ContextWindowOperationSummarize


def make_messages(*contents):
    return [MessageHuman(content = c) for c in contents]


class TestSummarize:
    def _summarizer(self, msgs):
        return "Summary: " + " | ".join(m.content for m in msgs)

    def test_compresses_first_n(self):
        msgs = make_messages("a", "b", "c", "d")
        result = ContextWindowOperationSummarize(n = 2, summarizer = self._summarizer).apply(msgs)
        assert len(result) == 3
        assert isinstance(result[0], MessageSystem)
        assert "a" in result[0].content
        assert "b" in result[0].content

    def test_remainder_preserved(self):
        msgs = make_messages("a", "b", "c", "d")
        result = ContextWindowOperationSummarize(n = 2, summarizer = self._summarizer).apply(msgs)
        assert result[1].content == "c"
        assert result[2].content == "d"

    def test_summarize_all(self):
        msgs = make_messages("a", "b")
        result = ContextWindowOperationSummarize(n = 2, summarizer = self._summarizer).apply(msgs)
        assert len(result) == 1
        assert isinstance(result[0], MessageSystem)

    def test_operation_type(self):
        op = ContextWindowOperationSummarize(n = 1, summarizer = lambda m: "s")
        assert op.operation_type == ContextWindowOperationType.SUMMARIZE
