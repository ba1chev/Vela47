import pytest
from pydantic import BaseModel

from app.intelligence.messages import MessageAI
from app.intelligence.outputs import OutputEntry
from tests.fixtures.outputs.contact import Contact
from app.intelligence.outputs import OutputParserType
from tests.fixtures.outputs.sentiment import Sentiment
from app.intelligence.outputs import OutputParserFactory
from app.intelligence.outputs import OUTPUT_PARSER_REGISTRY


class TestOutputParserFactory:
    def setup_method(self):
        self.factory = OutputParserFactory()

    def test_all_types_registered(self):
        for parser_type in OutputParserType:
            assert parser_type in OUTPUT_PARSER_REGISTRY

    def test_creates_text_parser(self):
        parser = self.factory.create(OutputParserType.TEXT)
        assert parser.parser_type == OutputParserType.TEXT

    def test_creates_json_parser(self):
        parser = self.factory.create(OutputParserType.JSON)
        assert parser.parser_type == OutputParserType.JSON

    def test_creates_list_parser_with_delimiter(self):
        parser = self.factory.create(OutputParserType.LIST, delimiter = "|")
        result = parser.parse(MessageAI(content = "a|b|c"))
        assert result.items == ["a", "b", "c"]

    def test_creates_structured_parser(self):
        parser = self.factory.create(OutputParserType.STRUCTURED, schema = Contact)
        assert parser.parser_type == OutputParserType.STRUCTURED

    def test_creates_classification_parser(self):
        parser = self.factory.create(OutputParserType.CLASSIFICATION, entry_type = Sentiment)
        assert parser.parser_type == OutputParserType.CLASSIFICATION

    def test_unknown_type_raises(self):
        with pytest.raises((ValueError, KeyError)):
            self.factory.create("nonexistent")
