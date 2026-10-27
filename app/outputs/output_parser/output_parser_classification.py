import json
from typing import Generic, TypeVar

from app.messages.message_ai import MessageAI
from app.outputs.output_entry import OutputEntry
from app.outputs.output_classification import OutputClassification
from app.outputs.output_parser.output_parser_base import OutputParserBase
from app.outputs.output_parser.output_parser_type import OutputParserType

T = TypeVar("T", bound = OutputEntry)


class OutputParserClassification(OutputParserBase, Generic[T]):
    """Parses the MessageAI content as a single classification choice drawn from
    a closed OutputEntry vocabulary. The model is expected to return a JSON
    object with a "selected" key whose value is one of the enum member strings.
    Pydantic validates the value against the declared members of T at construction
    time, raising a ValueError for anything outside the vocabulary — the same
    guarantee as constrained decoding, enforced on the client side as a
    defence-in-depth measure. Supply the target enum at construction time:
    OutputParserClassification(entry_type=Intent)."""

    def __init__(self, entry_type: type[T]) -> None:
        self._entry_type = entry_type

    @property
    def parser_type(self) -> OutputParserType:
        return OutputParserType.CLASSIFICATION

    def parse(self, message: MessageAI) -> OutputClassification[T]:
        content = (
            message.content
            if isinstance(message.content, str)
            else str(message.content)
        )
        data = json.loads(content)
        selected = self._entry_type(data["selected"])
        return OutputClassification(raw = message, selected = selected)
