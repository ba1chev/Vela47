from abc import ABC, abstractmethod

from app.intelligence.agents import RagChunkerType


class RagChunkerBase(ABC):
    """Abstract base for cutting a document's text into the chunks that are embedded
    and indexed one by one. Every chunker shares two parameters: how long a chunk may be
    and how much consecutive chunks overlap. The overlap is what keeps a sentence that
    straddles a boundary findable from either side of it.

    Lengths are in characters, not tokens. Characters are what the server can measure
    without the embedding model's tokenizer, and that model's context is far larger than
    any chunk, so the approximation never truncates anything."""

    def __init__(self, chunk_chars: int = 800, overlap_chars: int = 120) -> None:
        if chunk_chars <= 0:
            raise ValueError("A chunk must be at least one character long.")
        if not 0 <= overlap_chars < chunk_chars:
            raise ValueError("The overlap must be shorter than a chunk and not negative.")

        self._chunk_chars: int = chunk_chars
        self._overlap_chars: int = overlap_chars

    @property
    @abstractmethod
    def chunker_type(self) -> RagChunkerType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def chunk(self, text: str) -> list[str]:
        raise NotImplementedError("Must be implemented")
