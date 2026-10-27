from typing import Any
from abc import ABC, abstractmethod

from app.outputs.output_parser.output_parser_base import OutputParserBase
from app.outputs.output_parser.output_parser_type import OutputParserType


class OutputParserBaseFactory(ABC):
    """Abstract factory that defines the contract for instantiating
    OutputParserBase objects. Subclasses implement create() to map each
    OutputParserType to its concrete parser class, keeping call sites
    decoupled from individual parser implementations."""

    @abstractmethod
    def create(self, type: OutputParserType, **kwargs: Any) -> OutputParserBase:
        raise NotImplementedError("Must be implemented")
