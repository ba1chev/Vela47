import json
import pytest

from app.intelligence.messages import MessageAI
from app.intelligence.outputs import OutputEntry
from app.intelligence.outputs import OutputParserType
from tests.fixtures.outputs.sentiment import Sentiment
from app.intelligence.outputs import OutputClassification
from app.intelligence.outputs import OutputParserClassification


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
