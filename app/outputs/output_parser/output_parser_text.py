from app.messages.message_ai import MessageAI
from app.outputs.output_text import OutputText
from app.outputs.output_parser.output_parser_base import OutputParserBase
from app.outputs.output_parser.output_parser_type import OutputParserType


class OutputParserText(OutputParserBase):
    """Extracts the raw string content of a MessageAI with no parsing or
    transformation. The content field may arrive as a plain str or as a list
    of content blocks; both cases are collapsed to a single string so callers
    always receive a uniform OutputText regardless of how the model returned
    its response."""

    @property
    def parser_type(self) -> OutputParserType:
        return OutputParserType.TEXT

    def parse(self, message: MessageAI) -> OutputText:
        content = (
            message.content
            if isinstance(message.content, str)
            else str(message.content)
        )
        return OutputText(raw = message, text = content)
