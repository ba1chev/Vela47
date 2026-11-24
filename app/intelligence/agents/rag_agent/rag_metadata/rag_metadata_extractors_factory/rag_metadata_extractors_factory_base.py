from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.agents import RagMetadataType
from app.intelligence.agents import RagMetadataExtractorBase


class RagMetadataExtractorsFactoryBase(ABC):
    """Abstract factory for RagMetadataExtractorBase instances. Lets
    RagMetadataAttacher name the metadata it works out by type, without importing the
    concrete extractors."""

    @abstractmethod
    def create(self, type: RagMetadataType, **kwargs: Any) -> RagMetadataExtractorBase:
        raise NotImplementedError("Must be implemented")
