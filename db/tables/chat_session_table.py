from typing import Any
from datetime import datetime
from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from db.tables.table_base import TableBase
from db.tables.utc_date_time import UtcDateTime
from db.tables.json_document import JSON_DOCUMENT


class ChatSessionTable(TableBase):
    """One row per conversation, with its messages kept in the row as a JSON list. A
    conversation is read whole every time an agent resumes it, so a separate messages
    table would add a join to every read for no query that needs one.

    owner_id deliberately has no foreign key to identity_entities: a guest owns
    conversations too, and a guest never has a row there. Listing one owner's
    conversations newest first is the query this table has to answer quickly, which is
    what the index is for."""

    __tablename__ = "chat_sessions"
    __table_args__ = (Index("ix_chat_sessions_owner_id_updated_at", "owner_id", "updated_at"),)

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key = True,
        comment = "Random hex id of the conversation."
    )
    owner_id: Mapped[str] = mapped_column(
        String(32),
        comment = "Id of the entity the conversation belongs to — a stored admin or user, or a guest."
    )
    title: Mapped[str] = mapped_column(
        String(200),
        comment = "Human-readable title shown in the list of conversations."
    )
    messages: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON_DOCUMENT,
        comment = "The ordered turns, each as model_dump(mode='json') of its message, without artifacts."
    )
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime(),
        comment = "When the conversation was started, in UTC."
    )
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime(),
        comment = "When a message was last appended, in UTC. Orders the list of conversations."
    )
