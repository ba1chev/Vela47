from pydantic import BaseModel, Field
from typing import Generic, Literal, TypeVar

from app.intelligence.outputs.output_type import OutputType
from app.intelligence.outputs.output_base.output_base import OutputBase

T = TypeVar("T", bound = BaseModel)


class OutputStructured(OutputBase, Generic[T]):
    """Wraps a model response parsed and validated against a specific Pydantic
    schema. The data field holds a fully validated instance of T, so callers
    get type-safe access to the model's output without manual parsing. Use this
    when the model is prompted with a JSON schema and the response must conform
    to a known structure — validation errors surface at parse time, not at the
    point of use."""

    type: Literal[OutputType.STRUCTURED] = OutputType.STRUCTURED
    data: T = Field(
        description = "The model's JSON response deserialised and validated into an instance "
            "of the Pydantic model T. Field types, required fields and constraints are "
            "enforced by Pydantic at construction time."
    )
