import pytest

from app.intelligence.outputs import OutputEntry
from tests.fixtures.outputs.sentiment import Sentiment


class TestOutputEntry:
    def test_is_string_enum(self):
        assert isinstance(Sentiment.POSITIVE, str)
        assert Sentiment.POSITIVE == "positive"

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            Sentiment("invalid")
