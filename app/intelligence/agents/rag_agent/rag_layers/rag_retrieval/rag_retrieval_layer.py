from app.intelligence.agents import RagContext
from app.intelligence.agents import RagLayerBase
from app.intelligence.agents import RagLayerType
from app.intelligence.memory import VectorDbMemory
from app.intelligence.memory import describe_entry
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.memory import reciprocal_rank_scores
from app.intelligence.memory import VectorDbOperationPolicy
from app.intelligence.tracing import current_tracing_service


class RagRetrievalLayer(RagLayerBase):
    """Finds the candidate passages for the query through the memory's retrieval policy,
    HybridSearchPolicy for documents, so both meaning and exact words count. It asks for
    more candidates than will be used, since reranking narrows them after.

    It searches twice, for the question and for the query layer's rewrite, and fuses the
    rankings with reciprocal_rank_fusion: a good rewrite makes a follow-up findable, and
    a bad one cannot lose what the question alone would have found. An empty memory
    costs no embedding call."""

    def __init__(self, vector_db_memory: VectorDbMemory,
        retrieval_policy: VectorDbOperationPolicy, candidates: int = 12) -> None:
        self._vector_db_memory: VectorDbMemory = vector_db_memory
        self._retrieval_policy: VectorDbOperationPolicy = retrieval_policy
        self._candidates: int = candidates

    @property
    def layer_type(self) -> RagLayerType:
        return RagLayerType.RETRIEVAL

    def execute(self, context: RagContext) -> None:
        goal = context.goal.content if isinstance(context.goal.content, str) else str(context.goal.content)
        queries = list(dict.fromkeys(
            current_query for current_query in (goal, context.query) if current_query
        ))
        tracer = current_tracing_service()
        rankings: list[list[VectorDbMemoryEntry]] = []
        for current_query in queries:
            with tracer.step(f"Search · {current_query}", "retrieval", {"query": current_query, "candidates": self._candidates}) as span:
                ranking = self._vector_db_memory.search_entries(current_query, self._candidates, self._retrieval_policy)
                span["found"] = len(ranking)
                span["detail"] = f"{len(ranking)} chunks over {len(self._vector_db_memory)} indexed"
            rankings.append(ranking)

        fused = reciprocal_rank_scores(rankings)[:self._candidates]
        context.candidates = [current for current, _ in fused]
        tracer.record("Candidates", "retrieval", {
            "detail": f"{len(fused)} candidates from {len(queries)} search(es), fused by reciprocal rank",
            "queries": queries,
            "candidates": [describe_entry(current, score) for current, score in fused]
        })
