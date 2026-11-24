from typing import Any

from app.intelligence.agents import RagSemanticScoringBase
from app.intelligence.agents import RagSemanticScoringType
from app.intelligence.agents import RAG_SEMANTIC_SCORING_REGISTRY
from app.intelligence.agents import RagSemanticScoringFactoryBase


class RagSemanticScoringFactory(RagSemanticScoringFactoryBase):
    """Concrete factory that maps each RagSemanticScoringType to its
    RagSemanticScoringBase subclass and delegates construction to it. Additional keyword
    arguments are forwarded verbatim, so the chunker sets the embeddings, the chunk
    length and the weights without the factory knowing them.

    Registry reference:
      TEXT_TILING -> RagSemanticScoringTextTiling(embeddings=<ModelEmbeddings>, chunk_chars=<int>,
                     window_sentences=<int>, default 3, and the weights)"""

    def create(self, type: RagSemanticScoringType, **kwargs: Any) -> RagSemanticScoringBase:
        cls = RAG_SEMANTIC_SCORING_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No semantic scoring class registered for type '{type}'. "
                f"Known types: {list(RAG_SEMANTIC_SCORING_REGISTRY)}"
            )

        return cls(**kwargs)
