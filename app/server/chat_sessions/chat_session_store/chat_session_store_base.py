from typing import Optional
from abc import ABC, abstractmethod

from app.intelligence.messages import MessageBase
from app.server.chat_sessions.chat_session import ChatSession


class ChatSessionStoreBase(ABC):
    """Abstract base for wherever conversations are kept. Like IdentityAccessStoreBase it
    only remembers: who may read or change a conversation is for the security pipeline
    to decide before a store is ever called, so nothing here checks ownership.

    append_messages() exists instead of a read followed by a write of the whole session
    because two turns appended at the same moment must both survive. Implementations
    have to make it atomic, and it raises KeyError for a conversation that does not exist
    rather than creating one implicitly."""

    @abstractmethod
    def create_session(self, chat_session: ChatSession) -> None:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def list_sessions(self, owner_id: str) -> list[ChatSession]:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def append_messages(self, session_id: str, messages: list[MessageBase]) -> ChatSession:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        raise NotImplementedError("Must be implemented")
