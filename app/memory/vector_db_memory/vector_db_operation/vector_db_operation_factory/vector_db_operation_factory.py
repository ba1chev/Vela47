from typing import Any

from app.memory.vector_db_memory.vector_db_operation.vector_db_operation import VectorDbOperation
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_type import VectorDbOperationType
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_factory.vector_db_operation_registry import VECTOR_DB_OPERATION_REGISTRY
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_factory.vector_db_operation_base_factory import VectorDbOperationBaseFactory


class VectorDbOperationFactory(VectorDbOperationBaseFactory):
    """Concrete factory that maps each VectorDbOperationType to its corresponding
    VectorDbOperation subclass and delegates construction to it. Additional keyword
    arguments are forwarded verbatim, so callers can supply operation-specific
    parameters without the factory needing to know about them explicitly.

    Registry reference:
      SEARCH      -> VectorDbOperationSearch(query_vector=<list[float]>, top_k=<int>)
      FILTER      -> VectorDbOperationFilter(predicate=<Callable[[VectorDbMemoryEntry], bool]>)
      RERANK      -> VectorDbOperationRerank(scorer=<Callable[[VectorDbMemoryEntry], float]>)
      DEDUPLICATE -> VectorDbOperationDeduplicate(threshold=<float>, default 0.95)"""

    def create(self, type: VectorDbOperationType, **kwargs: Any) -> VectorDbOperation:
        cls = VECTOR_DB_OPERATION_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No operation class registered for type '{type}'. "
                f"Known types: {list(VECTOR_DB_OPERATION_REGISTRY)}"
            )

        return cls(**kwargs)
