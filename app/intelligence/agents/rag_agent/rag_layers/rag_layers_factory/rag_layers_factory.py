from typing import Any

from app.intelligence.agents import RagLayerBase
from app.intelligence.agents import RagLayerType
from app.intelligence.agents import RAG_LAYERS_REGISTRY
from app.intelligence.agents import RagLayersFactoryBase


class RagLayersFactory(RagLayersFactoryBase):
    """Concrete factory that maps each RagLayerType to its RagLayerBase subclass and
    delegates construction to it. Additional keyword arguments are forwarded verbatim, so
    the policy supplies each layer's own dependencies — a model, a vector memory and its
    retrieval policy, a tracer — without the factory knowing which takes which.

    Registry reference:
      QUERY      -> RagQueryLayer(model=<ModelFoundation>)
      RETRIEVAL  -> RagRetrievalLayer(vector_db_memory=<VectorDbMemory>,
                    retrieval_policy=<VectorDbOperationPolicy>, candidates=<int>, default 12)
      RERANKING  -> RagRerankingLayer(model=<ModelFoundation>, top_n=<int>, default 4,
                    min_score=<int>, default 4)
      GENERATION -> RagGenerationLayer(model=<ModelFoundation>, tracing_service=<TracingServiceBase>)"""

    def create(self, type: RagLayerType, **kwargs: Any) -> RagLayerBase:
        cls = RAG_LAYERS_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No layer class registered for type '{type}'. "
                f"Known types: {list(RAG_LAYERS_REGISTRY)}"
            )

        return cls(**kwargs)
