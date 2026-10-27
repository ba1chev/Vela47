from app.messages.message_ai import MessageAI
from app.messages.message_type import MessageType
from app.messages.message_usage_metadata import MessageUsageMetadata
from app.messages.message_tool_calls.message_tool_call import MessageToolCall


class TestMessageAI:
    def test_type_is_ai(self):
        msg = MessageAI(content = "response")
        assert msg.type == MessageType.AI_MESSAGE

    def test_str_representation(self):
        msg = MessageAI(content = "answer")
        assert str(msg) == "AI: answer"

    def test_tool_calls_default_empty(self):
        msg = MessageAI(content = "x")
        assert msg.tool_calls == []
        assert msg.invalid_tool_calls == []

    def test_usage_metadata_default_none(self):
        msg = MessageAI(content = "x")
        assert msg.usage_metadata is None

    def test_usage_metadata_attached(self):
        meta = MessageUsageMetadata(input_tokens = 10, output_tokens = 20, total_tokens = 30)
        msg = MessageAI(content = "x", usage_metadata = meta)
        assert msg.usage_metadata.total_tokens == 30

    def test_with_tool_call(self):
        call = MessageToolCall(name = "search", args = {"query": "python"}, id = "c1")
        msg = MessageAI(content = "", tool_calls = [call])
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].name == "search"
