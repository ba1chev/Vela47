from abc import ABC, abstractmethod

from app.intelligence.agents import RagMetadataType
from app.intelligence.agents import RagMetadataDocument
from app.intelligence.memory import VectorDbMemoryMetadata


class RagMetadataExtractorBase(ABC):
    """Abstract base for working out one kind of metadata for every chunk of a
    document. apply() takes the metadata so far, one per chunk in chunk order, and
    returns it with the field its type names filled in — the way a VectorDbOperation
    takes entries and returns them — so RagMetadataAttacher can run any set of
    extractors one after the other. The metadata is frozen, so each returns copies."""

    @property
    @abstractmethod
    def metadata_type(self) -> RagMetadataType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def apply(self, document: RagMetadataDocument,
        metadata: list[VectorDbMemoryMetadata]) -> list[VectorDbMemoryMetadata]:
        raise NotImplementedError("Must be implemented")
