import pytest

from app.intelligence.messages import MessageType
from app.intelligence.messages import MessageBase
from app.intelligence.memory import ContextWindow
from app.intelligence.memory import ShortTermMemory
from app.intelligence.memory import ContextWindowPolicy
from app.intelligence.memory import ContextWindowOperation
from tests.fixtures.memory.slide_policy import SlidePolicy
from app.intelligence.memory import ContextWindowOperationSlide
from tests.fixtures.memory.keep_all_policy import KeepAllPolicy


def make_memory(*contents):
    mem = ShortTermMemory()
    for c in contents:
        mem.append_message(c, MessageType.HUMAN_MESSAGE)
    return mem


class TestContextWindow:
    def test_starts_empty(self):
        mem = ShortTermMemory()
        cw = ContextWindow(memory = mem, max_window_size = 5)
        cw.set_policy(KeepAllPolicy())
        assert cw.is_empty()

    def test_build_after_update(self):
        mem = make_memory("a", "b", "c")
        cw = ContextWindow(memory = mem, max_window_size = 10)
        cw.set_policy(KeepAllPolicy())
        cw.update()
        assert len(cw.build()) == 3

    def test_is_full_when_at_capacity(self):
        mem = make_memory("a", "b", "c")
        cw = ContextWindow(memory = mem, max_window_size = 3)
        cw.set_policy(KeepAllPolicy())
        assert cw.is_full()

    def test_is_not_full_below_capacity(self):
        mem = make_memory("a", "b")
        cw = ContextWindow(memory = mem, max_window_size = 5)
        cw.set_policy(KeepAllPolicy())
        assert not cw.is_full()

    def test_fits_returns_true_when_room(self):
        from app.intelligence.messages import MessageHuman
        mem = make_memory("a")
        cw = ContextWindow(memory = mem, max_window_size = 5)
        cw.set_policy(KeepAllPolicy())
        assert cw.fits(MessageHuman(content = "new"))

    def test_fits_returns_false_when_full(self):
        from app.intelligence.messages import MessageHuman
        mem = make_memory("a", "b", "c", "d", "e")
        cw = ContextWindow(memory = mem, max_window_size = 5)
        cw.set_policy(KeepAllPolicy())
        assert not cw.fits(MessageHuman(content = "new"))

    def test_size_reflects_buffer(self):
        mem = make_memory("a", "b", "c")
        cw = ContextWindow(memory = mem, max_window_size = 10)
        cw.set_policy(KeepAllPolicy())
        cw.update()
        assert cw.size() == 3

    def test_policy_applied_when_full(self):
        mem = make_memory("a", "b", "c", "d", "e")
        cw = ContextWindow(memory = mem, max_window_size = 5)
        cw.set_policy(SlidePolicy())
        cw.update()
        result = cw.build()
        assert len(result) == 3
        assert result[0].content == "c"

    def test_policy_not_applied_below_capacity(self):
        mem = make_memory("a", "b", "c")
        cw = ContextWindow(memory = mem, max_window_size = 10)
        cw.set_policy(SlidePolicy())
        cw.update()
        assert len(cw.build()) == 3

    def test_build_returns_empty_before_update(self):
        mem = make_memory("a", "b")
        cw = ContextWindow(memory = mem, max_window_size = 10)
        cw.set_policy(KeepAllPolicy())
        assert cw.build() == []
