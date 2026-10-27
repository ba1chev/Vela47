from app.messages.message_ai import MessageAI
from app.outputs.output_parser.output_parser_type import OutputParserType
from app.outputs.output_parser.output_parser_list import OutputParserList


class TestOutputParserList:
    def test_parser_type(self):
        assert OutputParserList().parser_type == OutputParserType.LIST

    def test_splits_on_newline(self):
        result = OutputParserList().parse(MessageAI(content = "apple\nbanana\ncherry"))
        assert result.items == ["apple", "banana", "cherry"]

    def test_custom_delimiter(self):
        result = OutputParserList(delimiter = ", ").parse(MessageAI(content = "one, two, three"))
        assert result.items == ["one", "two", "three"]

    def test_strips_whitespace(self):
        result = OutputParserList().parse(MessageAI(content = "  a  \n  b  \n  c  "))
        assert result.items == ["a", "b", "c"]

    def test_ignores_empty_lines(self):
        result = OutputParserList().parse(MessageAI(content = "a\n\nb\n\nc"))
        assert result.items == ["a", "b", "c"]
