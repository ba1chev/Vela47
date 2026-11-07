from typing import Any

from app.intelligence.memory import VectorDbOperation
from app.intelligence.memory import VectorDbOperationType
from app.intelligence.memory import VECTOR_DB_OPERATION_REGISTRY
from app.intelligence.memory import VectorDbOperationBaseFactory


class VectorDbOperationFactory(VectorDbOperationBaseFactory):
    """Concrete factory that maps each VectorDbOperationType to its corresponding
    VectorDbOperation subclass and delegates construction to it. Additional keyword
    arguments are forwarded verbatim, so callers can supply operation-specific
    parameters without the factory needing to know about them explicitly.

    Registry reference:
      SEARCH      -> VectorDbOperationSearch(query_vector=<list[float]>, top_k=<int>)
      FILTER      -> VectorDbOperationFilter(predicate=<Callable[[VectorDbMemoryEntry], bool]>)
      RERANK      -> VectorDbOperationRerank(scorer=<Callable[[VectorDbMemoryEntry], float]>)
      DEDUPLICATE -> VectorDbOperationDeduplicate(threshold=<float>, default 0.95)
      KEYWORD_SEARCH -> VectorDbOperationKeywordSearch(query=<str>, top_k=<int>)
      HYBRID_SEARCH -> VectorDbOperationHybridSearch(query=<str>, query_vector=<list[float]>,
                       top_k=<int>, rank_constant=<int>, default 60)"""

    def create(self, type: VectorDbOperationType, **kwargs: Any) -> VectorDbOperation:
        cls = VECTOR_DB_OPERATION_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No operation class registered for type '{type}'. "
                f"Known types: {list(VECTOR_DB_OPERATION_REGISTRY)}"
            )

        return cls(**kwargs)
