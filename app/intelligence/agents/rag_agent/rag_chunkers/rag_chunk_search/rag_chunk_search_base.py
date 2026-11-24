from abc import ABC, abstractmethod

from app.intelligence.agents import RagChunkSearchType


class RagChunkSearchBase(ABC):
    """Abstract base for choosing all the cuts of one document together. The document is
    its sentences' lengths; cutting before sentence i costs cut_costs[i], and adding
    sentence i to a chunk that starts at sentence s costs extend_costs[(s, i)].
    search() returns the sentences that start a chunk, the first always among them.

    The length limits are hard and given at construction, so one instance cuts many
    documents: no chunk is longer than chunk_chars, and none is shorter than min_chars
    unless the next sentence would not fit. The costs are the chunker's own (see
    RagChunkerSemantic)."""

    def __init__(self, chunk_chars: int, min_chars: int) -> None:
        if chunk_chars <= 0:
            raise ValueError("A chunk must be at least one character long.")
        if not 0 <= min_chars <= chunk_chars:
            raise ValueError("The shortest chunk must be between zero and the longest chunk.")

        self._chunk_chars: int = chunk_chars
        self._min_chars: int = min_chars

    @property
    @abstractmethod
    def search_type(self) -> RagChunkSearchType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def search(self, lengths: list[int], cut_costs: list[float],
        extend_costs: dict[tuple[int, int], float]) -> list[int]:
        raise NotImplementedError("Must be implemented")
