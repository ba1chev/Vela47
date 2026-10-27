from app.messages.message_tool_calls.message_tool_call import MessageToolCall


class TestMessageToolCall:
    def test_fields(self):
        call = MessageToolCall(name = "add", args = {"a": 1, "b": 2}, id = "x1")
        assert call.name == "add"
        assert call.args == {"a": 1, "b": 2}
        assert call.id == "x1"

    def test_id_defaults_none(self):
        call = MessageToolCall(name = "fn", args = {})
        assert call.id is None

    def test_type_literal(self):
        call = MessageToolCall(name = "fn", args = {})
        assert call.type == "tool_call"
