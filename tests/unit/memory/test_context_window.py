import pytest

from app.messages.message_type import MessageType
from app.messages.message_base.message_base import MessageBase
from app.memory.short_term_memory.short_term_memory import ShortTermMemory
from app.memory.short_term_memory.context_window.context_window import ContextWindow
from app.memory.short_term_memory.context_window.context_window_operation.context_window_policy import ContextWindowPolicy
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation import ContextWindowOperation
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_slide import ContextWindowOperationSlide


class KeepAllPolicy(ContextWindowPolicy):
    def resolve(self, messages, capacity):
        return []


class SlidePolicy(ContextWindowPolicy):
    def resolve(self, messages, capacity):
        return [ContextWindowOperationSlide(step = 2)]


def make_memory(*contents):
    mem = ShortTermMemory()
    for c in contents:
        mem.append_message(c, MessageType.HUMAN_MESSAGE)
    return mem


class TestContextWindow:
    def test_starts_empty(self):
        mem = ShortTermMemory()
        cw = ContextWindow(memory = mem, max_window_size = 5, policy = KeepAllPolicy())
        assert cw.is_empty()

    def test_build_after_update(self):
        mem = make_memory("a", "b", "c")
        cw = ContextWindow(memory = mem, max_window_size = 10, policy = KeepAllPolicy())
        cw.update()
        assert len(cw.build()) == 3

    def test_is_full_when_at_capacity(self):
        mem = make_memory("a", "b", "c")
        cw = ContextWindow(memory = mem, max_window_size = 3, policy = KeepAllPolicy())
        assert cw.is_full()

    def test_is_not_full_below_capacity(self):
        mem = make_memory("a", "b")
        cw = ContextWindow(memory = mem, max_window_size = 5, policy = KeepAllPolicy())
        assert not cw.is_full()

    def test_fits_returns_true_when_room(self):
        from app.messages.message_human import MessageHuman
        mem = make_memory("a")
        cw = ContextWindow(memory = mem, max_window_size = 5, policy = KeepAllPolicy())
        assert cw.fits(MessageHuman(content = "new"))

    def test_fits_returns_false_when_full(self):
        from app.messages.message_human import MessageHuman
        mem = make_memory("a", "b", "c", "d", "e")
        cw = ContextWindow(memory = mem, max_window_size = 5, policy = KeepAllPolicy())
        assert not cw.fits(MessageHuman(content = "new"))

    def test_size_reflects_buffer(self):
        mem = make_memory("a", "b", "c")
        cw = ContextWindow(memory = mem, max_window_size = 10, policy = KeepAllPolicy())
        cw.update()
        assert cw.size() == 3

    def test_policy_applied_when_full(self):
        mem = make_memory("a", "b", "c", "d", "e")
        cw = ContextWindow(memory = mem, max_window_size = 5, policy = SlidePolicy())
        cw.update()
        result = cw.build()
        assert len(result) == 3
        assert result[0].content == "c"

    def test_policy_not_applied_below_capacity(self):
        mem = make_memory("a", "b", "c")
        cw = ContextWindow(memory = mem, max_window_size = 10, policy = SlidePolicy())
        cw.update()
        assert len(cw.build()) == 3

    def test_build_returns_empty_before_update(self):
        mem = make_memory("a", "b")
        cw = ContextWindow(memory = mem, max_window_size = 10, policy = KeepAllPolicy())
        assert cw.build() == []
