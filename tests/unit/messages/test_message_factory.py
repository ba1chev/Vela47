import pytest

from app.messages.message_ai import MessageAI
from app.messages.message_tool import MessageTool
from app.messages.message_type import MessageType
from app.messages.message_human import MessageHuman
from app.messages.message_system import MessageSystem
from app.messages.message_factory.message_factory import MessageFactory


class TestMessageFactory:
    def setup_method(self):
        self.factory = MessageFactory()

    def test_creates_human_message(self):
        msg = self.factory.create(MessageType.HUMAN_MESSAGE, "hello")
        assert isinstance(msg, MessageHuman)
        assert msg.content == "hello"

    def test_creates_ai_message(self):
        msg = self.factory.create(MessageType.AI_MESSAGE, "response")
        assert isinstance(msg, MessageAI)

    def test_creates_system_message(self):
        msg = self.factory.create(MessageType.SYSTEM_MESSAGE, "instruction")
        assert isinstance(msg, MessageSystem)

    def test_creates_tool_message(self):
        msg = self.factory.create(MessageType.TOOL_MESSAGE, "result", tool_call_id = "c1")
        assert isinstance(msg, MessageTool)

    def test_unknown_type_raises(self):
        with pytest.raises((ValueError, KeyError)):
            self.factory.create("unknown_type", "x")
