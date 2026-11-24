import math
from operator import mul
from abc import ABC, abstractmethod

from app.intelligence.model import ModelEmbeddings
from app.intelligence.agents import RagSemanticScoringType


class RagSemanticScoringBase(ABC):
    """Abstract base for pricing the cuts of a document from what its sentences mean.
    score() takes the sentences as the chunker split them and returns the costs a
    RagChunkSearchBase works on: cut_costs[i] for cutting before sentence i, and
    extend_costs[(s, i)] for adding sentence i to a chunk that starts at sentence s,
    for every chunk no longer than chunk_chars.

    _vectors() is what every semantic scoring shares: the sentences embedded in one
    batch and scaled to unit length, so a dot product is their cosine similarity."""

    def __init__(self, embeddings: ModelEmbeddings, chunk_chars: int) -> None:
        if chunk_chars <= 0:
            raise ValueError("A chunk must be at least one character long.")

        self._embeddings: ModelEmbeddings = embeddings
        self._chunk_chars: int = chunk_chars

    @property
    @abstractmethod
    def scoring_type(self) -> RagSemanticScoringType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def score(self, units: list[str]) -> tuple[list[float], dict[tuple[int, int], float]]:
        raise NotImplementedError("Must be implemented")

    def _vectors(self, units: list[str]) -> list[list[float]]:
        vectors = self._embeddings.embed_many([current_unit.strip() for current_unit in units])
        result: list[list[float]] = []
        for current_vector in vectors:
            norm = math.sqrt(sum(map(mul, current_vector, current_vector))) or 1.0
            result.append([value / norm for value in current_vector])
        return result
