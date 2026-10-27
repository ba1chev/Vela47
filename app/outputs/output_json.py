from pydantic import Field
from typing import Any, Literal

from app.outputs.output_type import OutputType
from app.outputs.output_base.output_base import OutputBase


class OutputJSON(OutputBase):
    """Wraps a model response parsed as a JSON object. The data field holds the
    deserialised Python dict, ready for further processing without an extra
    json.loads() call. Use this when the model is prompted to return a JSON
    object and the caller needs the raw key-value structure without committing
    to a specific Pydantic schema — for schema-validated responses prefer
    StructuredOutput."""

    type: Literal[OutputType.JSON] = OutputType.JSON
    data: dict[str, Any] = Field(
        description = "The model's JSON response deserialised into a Python dict. "
            "Keys and value types are exactly as the model produced them — no "
            "additional coercion or validation is applied beyond JSON parsing."
    )
