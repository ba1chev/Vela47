from enum import Enum


class VectorDbOperationType(Enum):
    """Enumerates the transformations that can be applied to a list of
    VectorDbMemoryEntry objects. Each value names a distinct retrieval or
    refinement strategy that the operation pipeline can execute to produce
    a focused, high-quality result set from the full vector store.

    SEARCH ranks by meaning, KEYWORD_SEARCH by the exact words, and HYBRID_SEARCH by
    both at once — the two fail in different places, which is why they are combined."""

    SEARCH = 1
    FILTER = 2
    RERANK = 3
    DEDUPLICATE = 4
    KEYWORD_SEARCH = 5
    HYBRID_SEARCH = 6
