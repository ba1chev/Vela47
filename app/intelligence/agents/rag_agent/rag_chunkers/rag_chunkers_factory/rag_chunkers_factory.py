from typing import Any

from app.intelligence.agents import RagChunkerBase
from app.intelligence.agents import RagChunkerType
from app.intelligence.agents import RAG_CHUNKERS_REGISTRY
from app.intelligence.agents import RagChunkersFactoryBase


class RagChunkersFactory(RagChunkersFactoryBase):
    """Concrete factory that maps each RagChunkerType to its RagChunkerBase subclass and
    delegates construction to it. Additional keyword arguments are forwarded verbatim,
    so the caller sets the chunk length and overlap without the factory knowing them.

    Registry reference:
      RECURSIVE -> RagChunkerRecursive(chunk_chars=<int>, default 800, overlap_chars=<int>, default 120)
      FIXED     -> RagChunkerFixed(chunk_chars=<int>, default 800, overlap_chars=<int>, default 120)"""

    def create(self, type: RagChunkerType, **kwargs: Any) -> RagChunkerBase:
        cls = RAG_CHUNKERS_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No chunker class registered for type '{type}'. "
                f"Known types: {list(RAG_CHUNKERS_REGISTRY)}"
            )

        return cls(**kwargs)
