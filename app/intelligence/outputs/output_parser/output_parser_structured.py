import re
from pydantic import BaseModel
from typing import Generic, TypeVar

from app.intelligence.messages import MessageAI
from app.intelligence.outputs import OutputStructured
from app.intelligence.outputs import OutputParserBase
from app.intelligence.outputs import OutputParserType

T = TypeVar("T", bound = BaseModel)


class OutputParserStructured(OutputParserBase, Generic[T]):
    """Validates the MessageAI content against a concrete Pydantic schema T.
    Delegates parsing and validation to model_validate_json so Pydantic raises
    a ValidationError immediately on any field mismatch, unknown key, or type
    coercion failure — rather than letting a malformed response propagate
    silently into the rest of the application. Supply the target schema at
    construction time: OutputParserStructured(schema=MyModel).

    A reply wrapped whole in a Markdown code block is unwrapped first: a model that
    was not held to the schema while decoding often writes its JSON that way."""

    CODE_BLOCK = re.compile(r"^\s*```[a-zA-Z]*\s*\n(.*?)\n?\s*```\s*$", re.DOTALL)

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
        block = self.CODE_BLOCK.match(content)
        data = self._schema.model_validate_json(block.group(1) if block else content)
        return OutputStructured(raw = message, data = data)
