import pytest

from app.outputs.output_entry import OutputEntry


class Sentiment(OutputEntry):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class TestOutputEntry:
    def test_is_string_enum(self):
        assert isinstance(Sentiment.POSITIVE, str)
        assert Sentiment.POSITIVE == "positive"

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            Sentiment("invalid")
