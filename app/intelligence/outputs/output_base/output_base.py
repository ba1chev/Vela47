from abc import ABC
from pydantic import Field

from app.intelligence.messages.message_ai import MessageAI
from app.intelligence.outputs.output_type import OutputType
from app.intelligence.messages.message_base.message_immutable_model import MessageImmutableModel


class OutputBase(MessageImmutableModel, ABC):
    """Abstract base for every structured output produced by an OutputParser.
    Mirrors the MessageBase pattern — each concrete subclass locks its type
    field to a Literal OutputType so routers and serialisers can dispatch
    without isinstance checks. The raw field preserves the originating
    MessageAI for traceability and downstream inspection."""

    type: OutputType = Field(
        description = "Discriminator that identifies the concrete output form. Each subclass "
            "locks this to a Literal value (OutputType.TEXT, OutputType.JSON, …) so the "
            "framework can route and deserialise outputs without isinstance checks."
    )
    raw: MessageAI = Field(
        description = "The unmodified MessageAI from which this output was parsed. Preserved "
            "for traceability — callers can inspect the original model response, tool calls, "
            "or usage metadata without reparsing."
    )
