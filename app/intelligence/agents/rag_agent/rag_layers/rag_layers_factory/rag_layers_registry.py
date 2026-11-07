from app.intelligence.agents import RagLayerBase
from app.intelligence.agents import RagLayerType
from app.intelligence.agents import RagQueryLayer
from app.intelligence.agents import RagRetrievalLayer
from app.intelligence.agents import RagRerankingLayer
from app.intelligence.agents import RagGenerationLayer


RAG_LAYERS_REGISTRY: dict[RagLayerType, type[RagLayerBase]] = {
    RagLayerType.QUERY: RagQueryLayer,
    RagLayerType.RETRIEVAL: RagRetrievalLayer,
    RagLayerType.RERANKING: RagRerankingLayer,
    RagLayerType.GENERATION: RagGenerationLayer
}
