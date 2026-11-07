from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.agents import RagChunkerBase
from app.intelligence.agents import RagChunkerType


class RagChunkersFactoryBase(ABC):
    """Abstract factory for RagChunkerBase instances. Lets the code that ingests
    documents name the chunking strategy it wants by type — the form a configuration
    value takes — without importing the concrete chunkers."""

    @abstractmethod
    def create(self, type: RagChunkerType, **kwargs: Any) -> RagChunkerBase:
        raise NotImplementedError("Must be implemented")
