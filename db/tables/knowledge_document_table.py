from datetime import datetime
from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db import TableBase
from db import UtcDateTime


class KnowledgeDocumentTable(TableBase):
    """One row per document a user uploaded for the RAG agent — what the document is,
    not what it says. The text lives in knowledge_chunks, already cut and embedded;
    this row is what the sidebar lists and what the storage limit is counted from, so
    neither has to touch the chunks.

    Like chat_sessions, owner_id has no foreign key: a guest uploads documents too, and
    a guest never has a row in identity_entities."""

    __tablename__ = "knowledge_documents"
    __table_args__ = (Index("ix_knowledge_documents_owner_id", "owner_id"),)

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key = True,
        comment = "Random hex id of the document."
    )
    owner_id: Mapped[str] = mapped_column(
        String(32),
        comment = "Id of the entity the document belongs to — a stored admin or user, or a guest."
    )
    title: Mapped[str] = mapped_column(
        String(200),
        comment = "Name the document is shown and cited under, normally its file name."
    )
    size_bytes: Mapped[int] = mapped_column(
        Integer,
        comment = "Size of the uploaded text in UTF-8 bytes. Summed per owner to enforce the storage limit."
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        comment = "How many chunks the document was cut into."
    )
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime(),
        comment = "When the document was uploaded, in UTC."
    )
