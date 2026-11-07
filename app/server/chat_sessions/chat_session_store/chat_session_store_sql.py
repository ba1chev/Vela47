from sqlalchemy import select
from typing import Any, Optional
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from db.database_base import DatabaseBase
from app.intelligence.messages import MessageBase
from app.intelligence.messages import MessageType
from app.intelligence.messages import MessageFactory
from app.intelligence.messages import MessageFactoryBase
from db.tables.chat_session_table import ChatSessionTable
from app.server.chat_sessions.chat_session import ChatSession
from app.server.chat_sessions.chat_session_store.chat_session_store_base import ChatSessionStoreBase


class ChatSessionStoreSql(ChatSessionStoreBase):
    """Keeps conversations in the chat_sessions table, one row each with the messages as
    a JSON list, and works the same over SQLite in DEV and PostgreSQL on RDS in PROD.

    Messages are written with model_dump in JSON mode — without artifact, the raw object
    a tool returned, which belongs to the process that ran the tool and was never part of
    the conversation — and read back through MessageFactory, which builds the right
    message class from the stored type.

    append_messages() reads the row with SELECT … FOR UPDATE, so on PostgreSQL a second
    append to the same conversation waits for the first to commit instead of overwriting
    it. SQLite ignores the clause; that is accepted for a development database with one
    person talking to it rather than worked around."""

    def __init__(self, database: DatabaseBase) -> None:
        self._database: DatabaseBase = database
        self._message_factory: MessageFactoryBase = MessageFactory()

    def _dump_messages(self, messages: list[MessageBase]) -> list[dict[str, Any]]:
        return [
            current_message.model_dump(mode = "json", exclude = {"artifact"})
            for current_message in messages
        ]

    def _load_messages(self, stored: list[dict[str, Any]]) -> list[MessageBase]:
        messages: list[MessageBase] = []
        for current_message in stored:
            fields = dict(current_message)
            message_type = MessageType(fields.pop("type"))
            messages.append(self._message_factory.create(message_type, fields.pop("content"), **fields))
        return messages

    def _to_chat_session(self, row: ChatSessionTable) -> ChatSession:
        return ChatSession(
            id = row.id,
            owner_id = row.owner_id,
            title = row.title,
            messages = self._load_messages(row.messages),
            created_at = row.created_at,
            updated_at = row.updated_at
        )

    def create_session(self, chat_session: ChatSession) -> None:
        try:
            with self._database.transaction() as transaction:
                transaction.add(ChatSessionTable(
                    id = chat_session.id,
                    owner_id = chat_session.owner_id,
                    title = chat_session.title,
                    messages = self._dump_messages(chat_session.messages),
                    created_at = chat_session.created_at,
                    updated_at = chat_session.updated_at
                ))
        except IntegrityError:
            raise ValueError(f"A chat session with id '{chat_session.id}' already exists.") from None

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        with self._database.transaction() as transaction:
            row = transaction.get(ChatSessionTable, session_id)
            return self._to_chat_session(row) if row is not None else None

    def list_sessions(self, owner_id: str) -> list[ChatSession]:
        with self._database.transaction() as transaction:
            rows = transaction.scalars(
                select(ChatSessionTable)
                .where(ChatSessionTable.owner_id == owner_id)
                .order_by(ChatSessionTable.updated_at.desc(), ChatSessionTable.id)
            ).all()
            return [self._to_chat_session(current_row) for current_row in rows]

    def append_messages(self, session_id: str, messages: list[MessageBase]) -> ChatSession:
        with self._database.transaction() as transaction:
            row = transaction.scalars(
                select(ChatSessionTable)
                .where(ChatSessionTable.id == session_id)
                .with_for_update()
            ).one_or_none()

            if row is None:
                raise KeyError(f"No chat session with id '{session_id}'.")

            row.messages = list(row.messages) + self._dump_messages(messages)
            row.updated_at = datetime.now(timezone.utc)
            return self._to_chat_session(row)

    def delete_session(self, session_id: str) -> bool:
        with self._database.transaction() as transaction:
            row = transaction.get(ChatSessionTable, session_id)
            if row is None:
                return False

            transaction.delete(row)
            return True
