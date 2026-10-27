from typing import Literal
from pydantic import Field

from app.outputs.output_type import OutputType
from app.outputs.output_base.output_base import OutputBase


class OutputList(OutputBase):
    """Wraps a model response parsed as an ordered list of strings. The items
    field holds the individual entries extracted from the model's output —
    typically by splitting on newlines, bullet markers, or a delimiter the
    prompt specified. Use this when the model is asked to enumerate things and
    the caller needs each item as a separate string rather than a single blob."""

    type: Literal[OutputType.LIST] = OutputType.LIST
    items: list[str] = Field(
        description = "Ordered list of string items extracted from the model's response. "
            "Each entry corresponds to one enumerated element as produced by the parser's "
            "splitting strategy — delimiter, newline, or bullet — with leading and trailing "
            "whitespace stripped."
    )
