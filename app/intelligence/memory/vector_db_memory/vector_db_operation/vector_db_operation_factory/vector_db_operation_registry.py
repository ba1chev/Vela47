from app.intelligence.memory import VectorDbOperation
from app.intelligence.memory import VectorDbOperationType
from app.intelligence.memory import VectorDbOperationSearch
from app.intelligence.memory import VectorDbOperationFilter
from app.intelligence.memory import VectorDbOperationRerank
from app.intelligence.memory import VectorDbOperationDeduplicate
from app.intelligence.memory import VectorDbOperationHybridSearch
from app.intelligence.memory import VectorDbOperationKeywordSearch


VECTOR_DB_OPERATION_REGISTRY: dict[VectorDbOperationType, type[VectorDbOperation]] = {
    VectorDbOperationType.SEARCH: VectorDbOperationSearch,
    VectorDbOperationType.FILTER: VectorDbOperationFilter,
    VectorDbOperationType.RERANK: VectorDbOperationRerank,
    VectorDbOperationType.DEDUPLICATE: VectorDbOperationDeduplicate,
    VectorDbOperationType.KEYWORD_SEARCH: VectorDbOperationKeywordSearch,
    VectorDbOperationType.HYBRID_SEARCH: VectorDbOperationHybridSearch
}
