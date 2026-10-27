import json
import pytest

from app.messages.message_ai import MessageAI
from app.outputs.output_entry import OutputEntry
from app.outputs.output_classification import OutputClassification
from app.outputs.output_parser.output_parser_type import OutputParserType
from app.outputs.output_parser.output_parser_classification import OutputParserClassification


class Sentiment(OutputEntry):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class TestOutputParserClassification:
    def setup_method(self):
        self.parser = OutputParserClassification(entry_type = Sentiment)

    def test_parser_type(self):
        assert self.parser.parser_type == OutputParserType.CLASSIFICATION

    def test_parses_valid_entry(self):
        result = self.parser.parse(MessageAI(content = json.dumps({"selected": "positive"})))
        assert isinstance(result, OutputClassification)
        assert result.selected == Sentiment.POSITIVE

    def test_invalid_entry_raises(self):
        with pytest.raises(ValueError):
            self.parser.parse(MessageAI(content = json.dumps({"selected": "unknown"})))
