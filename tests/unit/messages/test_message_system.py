from app.messages.message_type import MessageType
from app.messages.message_system import MessageSystem


class TestMessageSystem:
    def test_type_is_system(self):
        msg = MessageSystem(content = "You are helpful.")
        assert msg.type == MessageType.SYSTEM_MESSAGE

    def test_str_representation(self):
        msg = MessageSystem(content = "Be concise.")
        assert str(msg) == "System: Be concise."
