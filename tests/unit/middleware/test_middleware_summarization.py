from app.intelligence.memory import ContextWindow
from app.intelligence.messages import MessageType
from app.intelligence.memory import ShortTermMemory
from app.intelligence.messages import MessageSystem
from app.intelligence.middleware import MiddlewareSummarization


def make_window(count, max_size):
    memory = ShortTermMemory()
    for index in range(count):
        memory.append_message(str(index), MessageType.HUMAN_MESSAGE)
    return ContextWindow(memory = memory, max_window_size = max_size)


class TestMiddlewareSummarization:
    def test_compresses_the_oldest_into_one_system_message(self):
        window = make_window(5, 5)
        MiddlewareSummarization(n = 3, summarizer = lambda m: "summary").process(window)
        result = window.build()
        assert len(result) == 3
        assert isinstance(result[0], MessageSystem)
        assert result[0].content == "summary"

    def test_summarizer_receives_only_the_oldest(self):
        window = make_window(5, 5)
        seen = []
        MiddlewareSummarization(n = 2, summarizer = lambda m: seen.extend(m) or "s").process(window)
        assert [message.content for message in seen] == ["0", "1"]

    def test_remaining_messages_are_untouched(self):
        window = make_window(5, 5)
        MiddlewareSummarization(n = 2, summarizer = lambda m: "s").process(window)
        assert [message.content for message in window.build()[1:]] == ["2", "3", "4"]

    def test_below_capacity_the_summarizer_is_never_called(self):
        """Summarising costs a model call, so it must not happen while there is room."""
        window = make_window(3, 10)
        calls = []
        MiddlewareSummarization(n = 2, summarizer = lambda m: calls.append(1) or "s").process(window)
        assert calls == []
