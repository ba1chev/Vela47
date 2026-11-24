from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.agents import RagChunkSearchBase
from app.intelligence.agents import RagChunkSearchType


class RagChunkSearchFactoryBase(ABC):
    """Abstract factory for RagChunkSearchBase instances. Lets a chunker name the search
    that chooses its cuts by type, without importing the concrete searches."""

    @abstractmethod
    def create(self, type: RagChunkSearchType, **kwargs: Any) -> RagChunkSearchBase:
        raise NotImplementedError("Must be implemented")
