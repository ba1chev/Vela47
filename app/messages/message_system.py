from typing import Literal

from app.messages.message_type import MessageType
from app.messages.message_base.message_base import MessageBase


class MessageSystem(MessageBase):
    """Carries the system prompt — standing instructions that shape the model's persona,
    constraints, output format, and any context it should treat as ground truth.
    Injected before all human and AI turns and is invisible to the end user."""

    type: Literal[MessageType.SYSTEM_MESSAGE] = MessageType.SYSTEM_MESSAGE

    def __str__(self) -> str:
        body = self.content if isinstance(self.content, str) else str(self.content)
        return f"System: {body}"
