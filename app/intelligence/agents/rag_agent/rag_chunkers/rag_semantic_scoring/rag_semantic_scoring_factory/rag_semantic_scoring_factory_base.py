from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.agents import RagSemanticScoringBase
from app.intelligence.agents import RagSemanticScoringType


class RagSemanticScoringFactoryBase(ABC):
    """Abstract factory for RagSemanticScoringBase instances. Lets the semantic chunker
    name the scoring that prices its cuts by type, without importing the concrete
    scorings."""

    @abstractmethod
    def create(self, type: RagSemanticScoringType, **kwargs: Any) -> RagSemanticScoringBase:
        raise NotImplementedError("Must be implemented")
