from typing import Any, Union

from app.messages.message_ai import MessageAI
from app.messages.message_type import MessageType
from app.messages.message_tool import MessageTool
from app.messages.message_human import MessageHuman
from app.messages.message_system import MessageSystem
from app.messages.message_base.message_base import MessageBase, ContentPart
from app.messages.message_factory.message_base_factory import MessageFactoryBase


class MessageFactory(MessageFactoryBase):
    """Concrete factory that maps each MessageType to its corresponding MessageBase
    subclass and delegates construction to it. Additional keyword arguments are
    forwarded verbatim, so callers can supply message-specific fields such as
    tool_call_id for MessageTool or example for MessageHuman without the factory
    needing to know about them explicitly."""

    _registry: dict[MessageType, type[MessageBase]] = {
        MessageType.HUMAN_MESSAGE: MessageHuman,
        MessageType.SYSTEM_MESSAGE: MessageSystem,
        MessageType.AI_MESSAGE: MessageAI,
        MessageType.TOOL_MESSAGE: MessageTool
    }

    def create(self, type: MessageType,
        content: Union[str, list[ContentPart]], **kwargs: Any) -> MessageBase:
        cls = self._registry.get(type)

        if cls is None:
            raise ValueError(
                f"No message class registered for type '{type}'. "
                f"Known types: {list(self._registry)}"
            )

        return cls(content = content, **kwargs)
