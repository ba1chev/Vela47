from enum import Enum


class RagLayerType(Enum):
    """Enumerates the stages a RagAgent pipeline can run. Each value maps to a concrete
    RagLayerBase subclass registered in RagLayersFactory, and the numeric values encode
    the canonical order: QUERY makes the question searchable on its own, RETRIEVAL finds
    candidate passages, RERANKING keeps the ones that actually answer it, and GENERATION
    writes the answer from them. A RagPolicy is free to select a subset."""

    QUERY = 0
    RETRIEVAL = 1
    RERANKING = 2
    GENERATION = 3
