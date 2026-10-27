from app.messages.message_ai import MessageAI
from app.outputs.output_list import OutputList
from app.outputs.output_parser.output_parser_base import OutputParserBase
from app.outputs.output_parser.output_parser_type import OutputParserType


class OutputParserList(OutputParserBase):
    """Splits the MessageAI content into an ordered list of strings using a
    configurable delimiter. Empty entries and surrounding whitespace are stripped
    so the items list contains only non-empty, trimmed strings regardless of
    how the model formatted its response. Supply the delimiter that matches the
    prompt's instruction — newline by default, but any character or substring
    works: OutputParserList(delimiter=", ")."""

    def __init__(self, delimiter: str = "\n") -> None:
        self._delimiter = delimiter

    @property
    def parser_type(self) -> OutputParserType:
        return OutputParserType.LIST

    def parse(self, message: MessageAI) -> OutputList:
        content = (
            message.content
            if isinstance(message.content, str)
            else str(message.content)
        )
        items = [item.strip() for item in content.split(self._delimiter) if item.strip()]
        return OutputList(raw = message, items = items)
