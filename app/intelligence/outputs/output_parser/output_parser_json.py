import json

from app.intelligence.messages.message_ai import MessageAI
from app.intelligence.outputs.output_json import OutputJSON
from app.intelligence.outputs.output_parser.output_parser_base import OutputParserBase
from app.intelligence.outputs.output_parser.output_parser_type import OutputParserType


class OutputParserJSON(OutputParserBase):
    """Deserialises the MessageAI content as a JSON object. Raises json.JSONDecodeError
    if the model returned something that is not valid JSON — callers should catch this
    or use a self-healing retry cycle to feed the error back to the model. Use this
    when the caller needs the raw key-value structure without committing to a Pydantic
    schema; for schema-validated responses prefer OutputParserStructured."""

    @property
    def parser_type(self) -> OutputParserType:
        return OutputParserType.JSON

    def parse(self, message: MessageAI) -> OutputJSON:
        content = (
            message.content
            if isinstance(message.content, str)
            else str(message.content)
        )
        data = json.loads(content)
        return OutputJSON(raw = message, data = data)
