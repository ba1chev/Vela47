from typing import Any

from app.intelligence.memory.memory_base import MemoryBase
from app.intelligence.messages.message_type import MessageType
from app.intelligence.messages.message_base.message_base import MessageBase
from app.intelligence.messages.message_factory.message_factory import MessageFactory
from app.intelligence.messages.message_factory.message_base_factory import MessageFactoryBase


class ShortTermMemory(MemoryBase):
    """Stateful store for the full conversation history of a single agent session.
    Accepts raw text and a MessageType, delegates construction to MessageFactory,
    and appends the resulting MessageBase to an ordered list. Acts as the single
    source of truth for all messages produced during a session — other components
    such as ContextWindow read from it but never write to it directly."""

    def __init__(self) -> None:
        self._messages_factory: MessageFactoryBase = MessageFactory()
        self._messages_container: list[MessageBase] = []

    def append_message(self, message: str, message_type: MessageType, **kwargs: Any) -> None:
        self._messages_container.append(
            self._messages_factory.create(
                message_type, message, **kwargs
            )
        )

    def get_all(self) -> list[MessageBase]:
        return list(self._messages_container)

    def __len__(self) -> int:
        return len(self._messages_container)

    def get_message(self, index: int) -> MessageBase:
        if index < 0 or index >= len(self._messages_container):
            raise IndexError(f"Index {index} is out of range for memory of size {len(self._messages_container)}")
        return self._messages_container[index]