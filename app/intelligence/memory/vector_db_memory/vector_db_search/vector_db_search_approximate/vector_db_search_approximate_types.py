from enum import Enum


class VectorDBSearchApproximateType(Enum):
    """The approximate nearest neighbour searches. HIERARCHICAL_NAVIGABLE_SMALL_WORLD
    (HNSW) walks a layered proximity graph and is the index pgvector, FAISS and most
    vector databases use."""

    HIERARCHICAL_NAVIGABLE_SMALL_WORLD = 0
