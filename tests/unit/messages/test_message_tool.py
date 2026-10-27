from app.messages.message_type import MessageType
from app.messages.message_tool import MessageTool


class TestMessageTool:
    def test_type_is_tool(self):
        msg = MessageTool(content = "result", tool_call_id = "c1")
        assert msg.type == MessageType.TOOL_MESSAGE

    def test_default_status_success(self):
        msg = MessageTool(content = "ok", tool_call_id = "c1")
        assert msg.status == "success"

    def test_error_status(self):
        msg = MessageTool(content = "fail", tool_call_id = "c1", status = "error")
        assert msg.status == "error"

    def test_artifact_stored(self):
        msg = MessageTool(content = "42", tool_call_id = "c1", artifact = 42)
        assert msg.artifact == 42

    def test_str_representation(self):
        msg = MessageTool(content = "done", tool_call_id = "abc")
        assert "abc" in str(msg)
        assert "done" in str(msg)

    def test_not_frozen(self):
        msg = MessageTool(content = "a", tool_call_id = "c1")
        msg.content = "b"
        assert msg.content == "b"
