from app.intelligence.agents import RagChunkSearchBase
from app.intelligence.agents import RagChunkSearchType
from app.intelligence.agents import RagChunkSearchAStar


RAG_CHUNK_SEARCH_REGISTRY: dict[RagChunkSearchType, type[RagChunkSearchBase]] = {
    RagChunkSearchType.A_STAR: RagChunkSearchAStar
}
