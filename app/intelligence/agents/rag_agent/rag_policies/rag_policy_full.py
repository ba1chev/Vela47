from typing import Optional

from app.intelligence.agents import RagPolicy
from app.intelligence.agents import RagLayerBase
from app.intelligence.agents import RagLayerType
from app.intelligence.model import ModelFoundation
from app.intelligence.memory import VectorDbMemory
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.agents import RagLayersFactoryBase
from app.intelligence.memory import VectorDbOperationPolicy


class RagPolicyFull(RagPolicy):
    """Runs the complete RAG pipeline — query, retrieve, rerank, generate.

    The three models are separate parameters for the same reason the DeepAgent's are:
    rewriting a query and scoring passages want a low temperature and short, exact
    replies, while generation wants a model that writes. Passing one instance three
    times is fine when that distinction does not matter.

    candidates is how many passages retrieval hands to reranking, top_n how many
    reranking hands to generation, and min_score the reranker score a passage needs to
    be kept at all."""

    def __init__(self, query_model: ModelFoundation, reranking_model: ModelFoundation,
        generation_model: ModelFoundation, vector_db_memory: VectorDbMemory,
        retrieval_policy: VectorDbOperationPolicy,
        tracing_service: Optional[TracingServiceBase] = None,
        candidates: int = 12, top_n: int = 4, min_score: int = 4) -> None:
        self._query_model: ModelFoundation = query_model
        self._reranking_model: ModelFoundation = reranking_model
        self._generation_model: ModelFoundation = generation_model
        self._vector_db_memory: VectorDbMemory = vector_db_memory
        self._retrieval_policy: VectorDbOperationPolicy = retrieval_policy
        self._tracing_service: Optional[TracingServiceBase] = tracing_service
        self._candidates: int = candidates
        self._top_n: int = top_n
        self._min_score: int = min_score

    def resolve(self, factory: RagLayersFactoryBase) -> list[RagLayerBase]:
        return [
            factory.create(RagLayerType.QUERY, model = self._query_model),
            factory.create(
                RagLayerType.RETRIEVAL,
                vector_db_memory = self._vector_db_memory,
                retrieval_policy = self._retrieval_policy,
                candidates = self._candidates
            ),
            factory.create(
                RagLayerType.RERANKING,
                model = self._reranking_model,
                top_n = self._top_n,
                min_score = self._min_score
            ),
            factory.create(
                RagLayerType.GENERATION,
                model = self._generation_model,
                tracing_service = self._tracing_service
            )
        ]
