from pydantic import BaseModel
from typing import Generic, TypeVar

from app.messages.message_ai import MessageAI
from app.outputs.output_structured import OutputStructured
from app.outputs.output_parser.output_parser_base import OutputParserBase
from app.outputs.output_parser.output_parser_type import OutputParserType

T = TypeVar("T", bound = BaseModel)


class OutputParserStructured(OutputParserBase, Generic[T]):
    """Validates the MessageAI content against a concrete Pydantic schema T.
    Delegates parsing and validation to model_validate_json so Pydantic raises
    a ValidationError immediately on any field mismatch, unknown key, or type
    coercion failure — rather than letting a malformed response propagate
    silently into the rest of the application. Supply the target schema at
    construction time: OutputParserStructured(schema=MyModel)."""

    def __init__(self, schema: type[T]) -> None:
        self._schema = schema

    @property
    def parser_type(self) -> OutputParserType:
        return OutputParserType.STRUCTURED

    def parse(self, message: MessageAI) -> OutputStructured[T]:
        content = (
            message.content
            if isinstance(message.content, str)
            else str(message.content)
        )
        data = self._schema.model_validate_json(content)
        return OutputStructured(raw = message, data = data)
