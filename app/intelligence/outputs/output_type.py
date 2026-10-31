from enum import Enum


class OutputType(Enum):
    """Enumerates the structured forms a model response can be parsed into.
    Each value corresponds to a concrete OutputBase subclass and an OutputParser
    that knows how to extract and validate that form from a raw MessageAI.

    CLASSIFICATION is a specialised form of STRUCTURED where T is an
    OutputEntry enum: the model chooses exactly one value from a closed set,
    enforced at the decoding level via the JSON schema "enum" constraint."""

    TEXT = 1
    JSON = 2
    STRUCTURED = 3
    LIST = 4
    CLASSIFICATION = 5
