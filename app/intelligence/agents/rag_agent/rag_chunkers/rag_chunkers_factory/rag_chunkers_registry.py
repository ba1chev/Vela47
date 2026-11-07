from app.intelligence.agents import RagChunkerBase
from app.intelligence.agents import RagChunkerType
from app.intelligence.agents import RagChunkerFixed
from app.intelligence.agents import RagChunkerRecursive


RAG_CHUNKERS_REGISTRY: dict[RagChunkerType, type[RagChunkerBase]] = {
    RagChunkerType.RECURSIVE: RagChunkerRecursive,
    RagChunkerType.FIXED: RagChunkerFixed
}
