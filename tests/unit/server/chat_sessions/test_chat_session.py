import pytest
from pydantic import ValidationError

from app.intelligence.messages import MessageAI
from app.server.chat_sessions import ChatSession
from app.intelligence.messages import MessageHuman
from app.intelligence.messages import MessageToolCall


class TestChatSession:
    def test_a_new_session_is_empty_and_titled(self):
        session = ChatSession(owner_id = "o1")
        assert session.messages == [] and session.title == "New chat"

    def test_a_new_session_was_last_updated_when_it_was_created(self):
        session = ChatSession(owner_id = "o1")
        assert session.updated_at == session.created_at

    def test_every_session_gets_its_own_id(self):
        assert ChatSession(owner_id = "o1").id != ChatSession(owner_id = "o1").id

    def test_an_owner_is_required(self):
        with pytest.raises(ValidationError):
            ChatSession(owner_id = "")

    def test_an_overlong_title_is_refused(self):
        with pytest.raises(ValidationError):
            ChatSession(owner_id = "o1", title = "x" * 201)

    def test_messages_keep_their_own_class(self):
        session = ChatSession(owner_id = "o1", messages = [MessageHuman(content = "hi"), MessageAI(content = "hello")])
        assert [type(current).__name__ for current in session.messages] == ["MessageHuman", "MessageAI"]

    def test_a_dump_keeps_the_fields_only_an_ai_message_has(self):
        message = MessageAI(content = "x", tool_calls = [MessageToolCall(name = "t", args = {}, id = "c")])
        dumped = ChatSession(owner_id = "o1", messages = [message]).model_dump()
        assert dumped["messages"][0]["tool_calls"][0]["name"] == "t"

    def test_the_vrn_puts_the_owner_where_the_user_role_grants_by_principal_id(self):
        session = ChatSession(owner_id = "o1", id = "s1")
        assert session.vrn == "vrn:session:o1:session/s1"

    def test_sessions_are_frozen(self):
        with pytest.raises(ValidationError):
            ChatSession(owner_id = "o1").title = "renamed"
