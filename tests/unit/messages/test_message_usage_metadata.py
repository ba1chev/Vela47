from app.messages.message_usage_metadata import MessageUsageMetadata


class TestMessageUsageMetadata:
    def test_fields(self):
        m = MessageUsageMetadata(input_tokens = 5, output_tokens = 10, total_tokens = 15)
        assert m.input_tokens == 5
        assert m.output_tokens == 10
        assert m.total_tokens == 15
