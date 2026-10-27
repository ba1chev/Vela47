from enum import Enum


class OutputParserType(Enum):
    """Enumerates the available output parser strategies. Each value maps to a
    concrete OutputParserBase subclass registered in OutputParserFactory and
    determines how a raw MessageAI is transformed into a typed OutputBase."""

    TEXT = 1
    JSON = 2
    STRUCTURED = 3
    LIST = 4
    CLASSIFICATION = 5
