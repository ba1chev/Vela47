from typing import Literal
from pydantic import Field

from app.intelligence.messages.message_type import MessageType
from app.intelligence.messages.message_base.message_base import MessageBase


class MessageHuman(MessageBase):
    """Represents a single turn from the human side of the conversation. This is the
    primary way to pass user input to the model — either as plain text or as a list of
    multimodal content blocks (text, images, …). Optionally flagged as a few-shot example
    when it is part of a demonstration prefix rather than a live dialogue turn."""
    type: Literal[MessageType.HUMAN_MESSAGE] = MessageType.HUMAN_MESSAGE
    example: bool = Field(
        default = False,
        description = "When True, this message is treated as a few-shot demonstration rather than "
            "a live turn. Few-shot messages are injected into the prompt to show the model the "
            "expected input/output pattern and are never treated as part of the active dialogue."
    )

    def __str__(self) -> str:
        body = self.content if isinstance(self.content, str) else str(self.content)
        return f"Human: {body}"
