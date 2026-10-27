from typing import Literal
from pydantic import Field

from app.outputs.output_type import OutputType
from app.outputs.output_base.output_base import OutputBase


class OutputText(OutputBase):
    """Wraps a plain-text model response. The text field holds the raw string
    content of the MessageAI as-is, with no parsing or transformation applied.
    Use this when the model is expected to reply in free-form prose and the
    caller wants the content in a typed container rather than accessing
    MessageAI.content directly."""

    type: Literal[OutputType.TEXT] = OutputType.TEXT
    text: str = Field(
        description = "The model's response as a plain string, extracted directly from "
            "MessageAI.content. No parsing, stripping or post-processing is applied."
    )
