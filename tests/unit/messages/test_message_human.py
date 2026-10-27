import pytest
from pydantic import ValidationError

from app.messages.message_type import MessageType
from app.messages.message_human import MessageHuman


class TestMessageHuman:
    def test_type_is_human(self):
        msg = MessageHuman(content = "hello")
        assert msg.type == MessageType.HUMAN_MESSAGE

    def test_str_representation(self):
        msg = MessageHuman(content = "hi")
        assert str(msg) == "Human: hi"

    def test_content_stored(self):
        msg = MessageHuman(content = "test content")
        assert msg.content == "test content"

    def test_immutable(self):
        msg = MessageHuman(content = "hello")
        with pytest.raises(ValidationError):
            msg.content = "changed"

    def test_optional_fields_default(self):
        msg = MessageHuman(content = "x")
        assert msg.id is None
        assert msg.name is None
        assert msg.additional_kwargs == {}
