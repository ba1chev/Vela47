from app.memory.vector_db_memory.vector_db_operation.vector_db_operation import VectorDbOperation
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_type import VectorDbOperationType
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_search import VectorDbOperationSearch
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_filter import VectorDbOperationFilter
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_rerank import VectorDbOperationRerank
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_deduplicate import VectorDbOperationDeduplicate


VECTOR_DB_OPERATION_REGISTRY: dict[VectorDbOperationType, type[VectorDbOperation]] = {
    VectorDbOperationType.SEARCH: VectorDbOperationSearch,
    VectorDbOperationType.FILTER: VectorDbOperationFilter,
    VectorDbOperationType.RERANK: VectorDbOperationRerank,
    VectorDbOperationType.DEDUPLICATE: VectorDbOperationDeduplicate
}
