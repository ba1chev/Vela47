from typing import Any

from app.intelligence.agents import RagChunkSearchBase
from app.intelligence.agents import RagChunkSearchType
from app.intelligence.agents import RAG_CHUNK_SEARCH_REGISTRY
from app.intelligence.agents import RagChunkSearchFactoryBase


class RagChunkSearchFactory(RagChunkSearchFactoryBase):
    """Concrete factory that maps each RagChunkSearchType to its RagChunkSearchBase
    subclass and delegates construction to it. Additional keyword arguments are
    forwarded verbatim, so the chunker sets the length limits without the factory
    knowing them.

    Registry reference:
      A_STAR -> RagChunkSearchAStar(chunk_chars=<int>, min_chars=<int>)"""

    def create(self, type: RagChunkSearchType, **kwargs: Any) -> RagChunkSearchBase:
        cls = RAG_CHUNK_SEARCH_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No chunk search class registered for type '{type}'. "
                f"Known types: {list(RAG_CHUNK_SEARCH_REGISTRY)}"
            )

        return cls(**kwargs)
