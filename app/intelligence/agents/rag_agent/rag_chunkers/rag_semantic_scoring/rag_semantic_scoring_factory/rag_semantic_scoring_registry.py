from app.intelligence.agents import RagSemanticScoringBase
from app.intelligence.agents import RagSemanticScoringType
from app.intelligence.agents import RagSemanticScoringTextTiling


RAG_SEMANTIC_SCORING_REGISTRY: dict[RagSemanticScoringType, type[RagSemanticScoringBase]] = {
    RagSemanticScoringType.TEXT_TILING: RagSemanticScoringTextTiling
}
