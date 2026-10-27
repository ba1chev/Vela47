from abc import ABC, abstractmethod

from app.messages.message_ai import MessageAI
from app.outputs.output_base.output_base import OutputBase
from app.outputs.output_parser.output_parser_type import OutputParserType


class OutputParserBase(ABC):
    """Abstract base for every output parser. Each concrete subclass implements
    one parsing strategy — plain text extraction, JSON deserialisation, Pydantic
    validation, or list splitting — and encapsulates the parameters it needs at
    construction time (e.g. a Pydantic schema for STRUCTURED, a delimiter for
    LIST). parse() is a pure function: it receives a MessageAI and returns a
    typed OutputBase, never calling the model or mutating shared state."""

    @property
    @abstractmethod
    def parser_type(self) -> OutputParserType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def parse(self, message: MessageAI) -> OutputBase:
        raise NotImplementedError("Must be implemented")
