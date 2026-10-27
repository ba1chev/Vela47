import pytest

from app.messages.message_type import MessageType
from app.messages.message_human import MessageHuman
from app.messages.message_ai import MessageAI
from app.memory.short_term_memory.short_term_memory import ShortTermMemory


class TestShortTermMemory:
    def setup_method(self):
        self.memory = ShortTermMemory()

    def test_starts_empty(self):
        assert len(self.memory) == 0

    def test_append_human_message(self):
        self.memory.append_message("hello", MessageType.HUMAN_MESSAGE)
        assert len(self.memory) == 1

    def test_append_ai_message(self):
        self.memory.append_message("response", MessageType.AI_MESSAGE)
        msg = self.memory.get_message(0)
        assert isinstance(msg, MessageAI)

    def test_get_message_correct_content(self):
        self.memory.append_message("test", MessageType.HUMAN_MESSAGE)
        msg = self.memory.get_message(0)
        assert msg.content == "test"

    def test_get_all_returns_all(self):
        self.memory.append_message("a", MessageType.HUMAN_MESSAGE)
        self.memory.append_message("b", MessageType.AI_MESSAGE)
        self.memory.append_message("c", MessageType.HUMAN_MESSAGE)
        all_msgs = self.memory.get_all()
        assert len(all_msgs) == 3

    def test_get_all_preserves_order(self):
        self.memory.append_message("first", MessageType.HUMAN_MESSAGE)
        self.memory.append_message("second", MessageType.AI_MESSAGE)
        all_msgs = self.memory.get_all()
        assert all_msgs[0].content == "first"
        assert all_msgs[1].content == "second"

    def test_get_message_out_of_range_raises(self):
        self.memory.append_message("x", MessageType.HUMAN_MESSAGE)
        with pytest.raises(IndexError):
            self.memory.get_message(5)

    def test_get_message_negative_index_raises(self):
        self.memory.append_message("x", MessageType.HUMAN_MESSAGE)
        with pytest.raises(IndexError):
            self.memory.get_message(-1)

    def test_multiple_messages_correct_types(self):
        self.memory.append_message("hi", MessageType.HUMAN_MESSAGE)
        self.memory.append_message("hello", MessageType.AI_MESSAGE)
        self.memory.append_message("system", MessageType.SYSTEM_MESSAGE)
        assert self.memory.get_message(0).type == MessageType.HUMAN_MESSAGE
        assert self.memory.get_message(1).type == MessageType.AI_MESSAGE
        assert self.memory.get_message(2).type == MessageType.SYSTEM_MESSAGE
