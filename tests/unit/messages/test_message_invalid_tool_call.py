from app.intelligence.messages import MessageInvalidToolCall


class TestMessageInvalidToolCall:
    def test_all_fields_optional(self):
        call = MessageInvalidToolCall()
        assert call.name is None
        assert call.args is None
        assert call.id is None
        assert call.error is None

    def test_with_error(self):
        call = MessageInvalidToolCall(name = "bad", error = "JSON parse error")
        assert call.error == "JSON parse error"
