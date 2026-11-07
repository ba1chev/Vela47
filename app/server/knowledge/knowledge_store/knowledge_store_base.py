from typing import Optional
from abc import ABC, abstractmethod

from app.server.knowledge import KnowledgeDocument
from app.intelligence.memory import VectorDbMemoryEntry


class KnowledgeStoreBase(ABC):
    """Abstract base for where uploaded documents and their indexed chunks are kept. Like
    the other stores it only remembers — ownership is checked by the security pipeline
    and the storage limit by the route — and it keeps a document and its chunks
    together: added as one unit and deleted as one unit, so a search can never find a
    chunk whose document is gone.

    load_entries() returns an owner's chunks ready to be searched, as VectorDbMemoryEntry
    carrying their stored vectors, so nothing is embedded twice."""

    @abstractmethod
    def add_document(self, document: KnowledgeDocument, entries: list[VectorDbMemoryEntry]) -> None:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def list_documents(self, owner_id: str) -> list[KnowledgeDocument]:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def load_entries(self, owner_id: str) -> list[VectorDbMemoryEntry]:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def used_bytes(self, owner_id: str) -> int:
        raise NotImplementedError("Must be implemented")
