from typing import Any

from app.intelligence.memory import VectorDBSearchApproximateBase
from app.intelligence.memory import VectorDBSearchApproximateType
from app.intelligence.memory import VectorDBSearchApproximateFactoryBase
from app.intelligence.memory import VECTOR_DB_SEARCH_APPROXIMATE_REGISTRY


class VectorDBSearchApproximateFactory(VectorDBSearchApproximateFactoryBase):
    """Concrete factory that maps each VectorDBSearchApproximateType to its class
    through VECTOR_DB_SEARCH_APPROXIMATE_REGISTRY. Keyword arguments are forwarded
    verbatim, so callers supply top_k, the vectors to index and any tuning parameter,
    such as HNSW's ef_search, without the factory knowing about them."""

    def create(self, type: VectorDBSearchApproximateType, **kwargs: Any) -> VectorDBSearchApproximateBase:
        cls = VECTOR_DB_SEARCH_APPROXIMATE_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No approximate search class registered for type '{type}'. "
                f"Known types: {list(VECTOR_DB_SEARCH_APPROXIMATE_REGISTRY)}"
            )

        return cls(**kwargs)
