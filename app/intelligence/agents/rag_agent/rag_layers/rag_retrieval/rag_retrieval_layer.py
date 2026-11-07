from app.intelligence.agents import RagContext
from app.intelligence.agents import RagLayerBase
from app.intelligence.agents import RagLayerType
from app.intelligence.memory import VectorDbMemory
from app.intelligence.memory import reciprocal_rank_fusion
from app.intelligence.memory import VectorDbOperationPolicy


class RagRetrievalLayer(RagLayerBase):
    """Finds the candidate passages for the query in the agent's VectorDbMemory, through
    whatever retrieval policy it was given — HybridSearchPolicy for documents, so that
    both the meaning of the question and its exact words count.

    It asks for more candidates than will be used. Retrieval is fast and approximate,
    reranking is slow and careful, and a passage that retrieval ranks tenth can still be
    the one that answers the question — so the net is cast wide here and narrowed after.
    An empty memory yields no candidates and costs no embedding call.

    It searches twice — for the question as asked and for the query layer's rewrite —
    and fuses the two rankings with reciprocal_rank_fusion. A rewrite is what makes a
    follow-up like 'how do I fix it?' findable, but a small model's rewrite is sometimes
    wrong, once even a stray phrase of its own instructions. Searching both means a good
    rewrite helps and a bad one cannot lose what the question alone would have found."""

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
        rankings = [
            self._vector_db_memory.search_entries(current_query, self._candidates, self._retrieval_policy)
            for current_query in queries
        ]
        context.candidates = reciprocal_rank_fusion(rankings)[:self._candidates]
