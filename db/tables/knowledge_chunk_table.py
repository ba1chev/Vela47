from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text

from db import TableBase
from db import JSON_DOCUMENT
from db import Float32Vector


class KnowledgeChunkTable(TableBase):
    """One row per chunk of an uploaded document: the passage verbatim, its embedding
    and the metadata worked out for it at upload. These rows are what the RAG agent
    searches — all of one owner's chunks are loaded into a VectorDbMemory for each
    question, which is what the owner index is for.

    owner_id is repeated from the document so that loading a user's knowledge is one
    indexed read instead of a join per question. Chunks are deleted together with their
    document by the store, explicitly, rather than relying on ON DELETE CASCADE, which
    SQLite ignores unless foreign keys are switched on for every connection."""

    __tablename__ = "knowledge_chunks"
    __table_args__ = (Index("ix_knowledge_chunks_owner_id", "owner_id"),)

    id: Mapped[str] = mapped_column(
        String(48),
        primary_key = True,
        comment = "'<document id>-<position>' — the id the RAG agent cites the passage by."
    )
    document_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("knowledge_documents.id", ondelete = "CASCADE"),
        comment = "The document this chunk was cut from."
    )
    owner_id: Mapped[str] = mapped_column(
        String(32),
        comment = "Owner of the document, repeated so one owner's chunks load without a join."
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        comment = "Position of the chunk within its document, from 0."
    )
    content: Mapped[str] = mapped_column(
        Text,
        comment = "The passage, verbatim as it appears in the document."
    )
    vector: Mapped[list[float]] = mapped_column(
        Float32Vector(),
        comment = "Embedding of the passage as packed float32 values."
    )
    span_start: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable = True,
        comment = "Offset in the document's text where the passage begins, if it is a verbatim slice."
    )
    span_end: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable = True,
        comment = "Offset in the document's text just past the passage's last character."
    )
    section: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable = True,
        comment = "Headings above the passage, outermost first, joined by ' › '."
    )
    topic: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable = True,
        comment = "The topic register's topic closest to the passage's embedding."
    )
    topic_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable = True,
        comment = "Cosine similarity between the passage's embedding and its topic."
    )
    keywords: Mapped[list[str]] = mapped_column(
        JSON_DOCUMENT,
        default = list,
        comment = "Words that set the passage apart from the rest of its document, as a JSON list."
    )
