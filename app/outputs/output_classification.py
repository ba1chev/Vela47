from pydantic import Field
from typing import Generic, Literal, TypeVar

from app.outputs.output_type import OutputType
from app.outputs.output_entry import OutputEntry
from app.outputs.output_base.output_base import OutputBase

T = TypeVar("T", bound = OutputEntry)


class OutputClassification(OutputBase, Generic[T]):
    """Wraps a model response parsed as a single value chosen from a closed
    OutputEntry enum. Because OutputEntry inherits from str and Enum, Pydantic
    emits the full member list as an "enum" array in the JSON schema; passing
    that schema to a constrained-decoding backend (Ollama, vLLM, …) restricts
    the model at the token level — it is physically unable to produce a value
    outside the declared set.

    T must be a concrete OutputEntry subclass that defines the classification
    vocabulary. The selected field holds the validated enum member, ready for
    direct dispatch without isinstance checks or string comparisons."""

    type: Literal[OutputType.CLASSIFICATION] = OutputType.CLASSIFICATION
    selected: T = Field(
        description = "The enum member the model selected from the OutputEntry "
            "vocabulary. Validated by Pydantic against the declared members of T "
            "so any value outside the closed set raises a ValidationError at "
            "parse time rather than silently propagating a hallucinated string."
    )
