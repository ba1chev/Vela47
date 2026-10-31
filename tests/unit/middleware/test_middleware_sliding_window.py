import pathlib

from app.intelligence.memory import ContextWindow
from app.intelligence.messages import MessageType
from app.intelligence.memory import ShortTermMemory
from app.intelligence.middleware import MiddlewareSlidingWindow


def make_window(count, max_size):
    memory = ShortTermMemory()
    for index in range(count):
        memory.append_message(str(index), MessageType.HUMAN_MESSAGE)
    return ContextWindow(memory = memory, max_window_size = max_size)


class TestMiddlewareSlidingWindow:
    def test_sets_a_policy_and_refreshes(self):
        window = make_window(5, 5)
        MiddlewareSlidingWindow(step = 2).process(window)
        assert len(window.build()) == 3

    def test_default_step_drops_one_exchange(self):
        window = make_window(5, 5)
        MiddlewareSlidingWindow().process(window)
        assert len(window.build()) == 3

    def test_step_of_one_drops_a_single_message(self):
        window = make_window(5, 5)
        MiddlewareSlidingWindow(step = 1).process(window)
        assert window.build()[0].content == "1"

    def test_below_capacity_nothing_is_dropped(self):
        window = make_window(3, 10)
        MiddlewareSlidingWindow(step = 2).process(window)
        assert len(window.build()) == 3

    def test_the_same_middleware_can_be_reused(self):
        middleware = MiddlewareSlidingWindow(step = 2)
        for _ in range(3):
            window = make_window(5, 5)
            middleware.process(window)
            assert len(window.build()) == 3
