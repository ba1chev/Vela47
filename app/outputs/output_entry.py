from enum import Enum


class OutputEntry(str, Enum):
    """Base class for all classification entry enums. Inheriting from both str
    and Enum ensures each member serialises as its string value, which Pydantic
    emits as an "enum" array in the JSON schema. Ollama (and other
    constrained-decoding backends) convert that schema into a grammar that
    prevents the model from producing any token sequence outside the declared
    set — making the classification physically impossible to hallucinate.

    Usage: subclass OutputEntry and declare the allowed values. Pass the
    subclass as the type parameter T to OutputClassification[T] so the parser
    and the model config share the same closed vocabulary."""

    pass
