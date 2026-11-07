from app.intelligence.memory import VectorDbOperation
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.memory import VectorDbOperationType
from app.intelligence.memory import reciprocal_rank_fusion
from app.intelligence.memory import VectorDbOperationSearch
from app.intelligence.memory import VectorDbOperationKeywordSearch


class VectorDbOperationHybridSearch(VectorDbOperation):
    """Ranks entries by meaning and by words at once, and keeps the top_k of both. It is
    built from the two single searches rather than beside them: VectorDbOperationSearch
    ranks every entry by cosine similarity to the query vector, VectorDbOperationKeyword
    Search ranks the ones sharing a word with the query by BM25, and the two rankings
    are fused with Reciprocal Rank Fusion.

    RRF is used because the two scores live on scales that cannot be compared — a cosine
    of 0.8 and a BM25 of 7.3 mean nothing to each other — while ranks can. Each entry
    scores 1 / (rank_constant + position) in every ranking it appears in, so a passage
    near the top of both beats one that leads only one, and the constant of 60 keeps a
    single first place from outweighing consistent agreement:
    VectorDbOperationHybridSearch(query="...", query_vector=vec, top_k=12)."""

    def __init__(self, query: str, query_vector: list[float], top_k: int,
        rank_constant: int = 60) -> None:
        self._query = query
        self._query_vector = query_vector
        self._top_k = top_k
        self._rank_constant = rank_constant

    @property
    def operation_type(self) -> VectorDbOperationType:
        return VectorDbOperationType.HYBRID_SEARCH

    def apply(self, entries: list[VectorDbMemoryEntry]) -> list[VectorDbMemoryEntry]:
        dense = VectorDbOperationSearch(query_vector = self._query_vector, top_k = len(entries)).apply(entries)
        lexical = VectorDbOperationKeywordSearch(query = self._query, top_k = len(entries)).apply(entries)
        return reciprocal_rank_fusion([dense, lexical], self._rank_constant)[:self._top_k]
