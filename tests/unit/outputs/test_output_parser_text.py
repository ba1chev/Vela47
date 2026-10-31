from app.intelligence.messages import MessageAI
from app.intelligence.outputs import OutputText
from app.intelligence.outputs import OutputParserType
from app.intelligence.outputs import OutputParserText


class TestOutputParserText:
    def setup_method(self):
        self.parser = OutputParserText()

    def test_parser_type(self):
        assert self.parser.parser_type == OutputParserType.TEXT

    def test_extracts_content(self):
        result = self.parser.parse(MessageAI(content = "hello world"))
        assert isinstance(result, OutputText)
        assert result.text == "hello world"

    def test_empty_content(self):
        result = self.parser.parse(MessageAI(content = ""))
        assert result.text == ""
