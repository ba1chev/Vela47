from app.intelligence.memory import tokenize
from app.intelligence.memory import describe_entry
from app.intelligence.memory import VectorDbOperation
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.memory import RANKING_TRACE_LIMIT
from app.intelligence.memory import VectorDbKeywordIndex
from app.intelligence.memory import VectorDbOperationType
from app.intelligence.tracing import current_tracing_service


class VectorDbOperationKeywordSearch(VectorDbOperation):
    """Ranks entries by BM25 against the query text and returns the top_k that share at
    least one word with it. The lexical counterpart of VectorDbOperationSearch: where
    that one ignores the words and compares meanings, this one compares words and knows
    nothing of meaning, so it finds the passage naming an exact identifier that a dense
    search would rank as merely related. An entry with no word in common scores zero and
    is left out rather than padded in at the bottom:
    VectorDbOperationKeywordSearch(query="ValueError in parse", top_k=10)."""

    def __init__(self, query: str, top_k: int) -> None:
        self._query = query
        self._top_k = top_k

    @property
    def operation_type(self) -> VectorDbOperationType:
        return VectorDbOperationType.KEYWORD_SEARCH

    def apply(self, entries: list[VectorDbMemoryEntry]) -> list[VectorDbMemoryEntry]:
        scores = VectorDbKeywordIndex(entries).scores(self._query)
        ranked = sorted(
            (current_pair for current_pair in zip(scores, range(len(entries))) if current_pair[0] > 0.0),
            key = lambda current_pair: current_pair[0],
            reverse = True
        )
        current_tracing_service().record("Keyword ranking", "retrieval", {
            "detail": f"{len(ranked)} of {len(entries)} chunks share a word with the query (BM25)",
            "terms": tokenize(self._query),
            "entries": len(entries),
            "matched": len(ranked),
            "ranking": [describe_entry(entries[current_index], score) for score, current_index in ranked[:RANKING_TRACE_LIMIT]]
        })
        return [entries[current_index] for _, current_index in ranked[:self._top_k]]
