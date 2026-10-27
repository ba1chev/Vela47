from app.messages.message_ai import MessageAI
from app.outputs.output_text import OutputText
from app.outputs.output_parser.output_parser_type import OutputParserType
from app.outputs.output_parser.output_parser_text import OutputParserText


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
