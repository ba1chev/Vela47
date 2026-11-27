from typing import Any, Optional
from sqlalchemy import delete, func, select, update

from db import DatabaseBase
from db import KnowledgeChunkTable
from db import KnowledgeDocumentTable
from app.server.knowledge import KnowledgeDocument
from app.intelligence.messages import MessageSystem
from app.server.knowledge import KnowledgeStoreBase
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.memory import VectorDbMemorySource
from app.intelligence.memory import VectorDbMemoryMetadata


class KnowledgeStoreSql(KnowledgeStoreBase):
    """Keeps documents and their chunks in knowledge_documents and knowledge_chunks, over
    SQLite in DEV and PostgreSQL on RDS in PROD.

    Chunks are written back exactly as RagIndexer made them and read back the same
    way: each as a MessageSystem whose id is the chunk id and whose name is the
    document's title, with its metadata in columns of its own — so a passage loaded from
    the database cites the same source it did the moment it was indexed. The title comes
    from the document row at load time, not from the chunk, so it is stored once.

    A document and its chunks are deleted in one transaction, chunks first, without
    relying on ON DELETE CASCADE, which SQLite ignores unless every connection switches
    foreign keys on."""

    def __init__(self, database: DatabaseBase) -> None:
        self._database: DatabaseBase = database

    def _to_document(self, row: KnowledgeDocumentTable) -> KnowledgeDocument:
        return KnowledgeDocument(
            id = row.id,
            owner_id = row.owner_id,
            title = row.title,
            size_bytes = row.size_bytes,
            chunk_count = row.chunk_count,
            created_at = row.created_at
        )

    def _to_metadata(self, row: KnowledgeChunkTable, title: str) -> VectorDbMemoryMetadata:
        return VectorDbMemoryMetadata(
            source = VectorDbMemorySource(
                document_id = row.document_id,
                title = title,
                chunk_index = row.chunk_index,
                start = row.span_start,
                end = row.span_end
            ),
            section = row.section,
            topic = row.topic,
            topic_score = row.topic_score,
            keywords = row.keywords or []
        )

    def add_document(self, document: KnowledgeDocument, entries: list[VectorDbMemoryEntry]) -> None:
        with self._database.transaction() as transaction:
            transaction.add(KnowledgeDocumentTable(
                id = document.id,
                owner_id = document.owner_id,
                title = document.title,
                size_bytes = document.size_bytes,
                chunk_count = document.chunk_count,
                created_at = document.created_at
            ))
            transaction.flush()
            transaction.add_all([
                KnowledgeChunkTable(
                    id = current_entry.message.id,
                    document_id = document.id,
                    owner_id = document.owner_id,
                    chunk_index = current_entry.metadata.source.chunk_index,
                    content = current_entry.message.content,
                    vector = current_entry.vector,
                    span_start = current_entry.metadata.source.start,
                    span_end = current_entry.metadata.source.end,
                    section = current_entry.metadata.section,
                    topic = current_entry.metadata.topic,
                    topic_score = current_entry.metadata.topic_score,
                    keywords = current_entry.metadata.keywords
                )
                for current_entry in entries
            ])

    def list_documents(self, owner_id: str) -> list[KnowledgeDocument]:
        with self._database.transaction() as transaction:
            rows = transaction.scalars(
                select(KnowledgeDocumentTable)
                .where(KnowledgeDocumentTable.owner_id == owner_id)
                .order_by(KnowledgeDocumentTable.created_at.desc(), KnowledgeDocumentTable.id)
            ).all()
            return [self._to_document(current_row) for current_row in rows]

    def get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        with self._database.transaction() as transaction:
            row = transaction.get(KnowledgeDocumentTable, document_id)
            return self._to_document(row) if row is not None else None

    def set_trace(self, document_id: str, trace: list[dict[str, Any]]) -> None:
        with self._database.transaction() as transaction:
            transaction.execute(
                update(KnowledgeDocumentTable).where(KnowledgeDocumentTable.id == document_id).values(trace = trace)
            )

    def get_trace(self, document_id: str) -> Optional[list[dict[str, Any]]]:
        with self._database.transaction() as transaction:
            return transaction.scalar(
                select(KnowledgeDocumentTable.trace).where(KnowledgeDocumentTable.id == document_id)
            )

    def delete_document(self, document_id: str) -> bool:
        with self._database.transaction() as transaction:
            row = transaction.get(KnowledgeDocumentTable, document_id)
            if row is None:
                return False

            transaction.execute(delete(KnowledgeChunkTable).where(KnowledgeChunkTable.document_id == document_id))
            transaction.delete(row)
            return True

    def load_entries(self, owner_id: str) -> list[VectorDbMemoryEntry]:
        with self._database.transaction() as transaction:
            rows = transaction.execute(
                select(KnowledgeChunkTable, KnowledgeDocumentTable.title)
                .join(KnowledgeDocumentTable, KnowledgeDocumentTable.id == KnowledgeChunkTable.document_id)
                .where(KnowledgeChunkTable.owner_id == owner_id)
                .order_by(KnowledgeChunkTable.document_id, KnowledgeChunkTable.chunk_index)
            ).all()
            return [
                VectorDbMemoryEntry(
                    message = MessageSystem(content = current_chunk.content, id = current_chunk.id, name = current_title),
                    vector = current_chunk.vector,
                    metadata = self._to_metadata(current_chunk, current_title)
                )
                for current_chunk, current_title in rows
            ]

    def used_bytes(self, owner_id: str) -> int:
        with self._database.transaction() as transaction:
            total = transaction.scalar(
                select(func.coalesce(func.sum(KnowledgeDocumentTable.size_bytes), 0))
                .where(KnowledgeDocumentTable.owner_id == owner_id)
            )
            return int(total or 0)
