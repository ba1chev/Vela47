from typing import Any, Union
from abc import ABC, abstractmethod

from app.intelligence.messages.message_type import MessageType
from app.intelligence.messages.message_base.message_base import MessageBase, ContentPart


class MessageFactoryBase(ABC):
    """Abstract factory that defines the contract for creating MessageBase instances.
    Subclasses implement create() to encapsulate the construction logic for each
    MessageType, keeping callers decoupled from the concrete message classes."""

    @abstractmethod
    def create(self, type: MessageType,
        content: Union[str, list[ContentPart]], **kwargs: Any) -> MessageBase:
        raise NotImplementedError("Must be implemented")
