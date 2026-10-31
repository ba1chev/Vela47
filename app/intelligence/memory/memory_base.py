from abc import ABC, abstractmethod

from app.intelligence.messages.message_type import MessageType
from app.intelligence.messages.message_base.message_base import MessageBase


class MemoryBase(ABC):
    @abstractmethod
    def append_message(self, message: str, message_type: MessageType) -> None:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def get_message(self, index: int) -> MessageBase:
        raise NotImplementedError("Must be implemented")