from typing import Any

from app.intelligence.memory import VectorDBSearchInformedBase
from app.intelligence.memory import VectorDBSearchInformedType
from app.intelligence.memory import VectorDBSearchInformedFactoryBase
from app.intelligence.memory import VECTOR_DB_SEARCH_INFORMED_REGISTRY


class VectorDBSearchInformedFactory(VectorDBSearchInformedFactoryBase):
    """Concrete factory that maps each VectorDBSearchInformedType to its class
    through VECTOR_DB_SEARCH_INFORMED_REGISTRY. Keyword arguments are forwarded
    verbatim, so callers supply the graph, the heuristics and any algorithm-specific
    parameter, such as BEAM_SEARCH's queue_limit, without the factory knowing them."""

    def create(self, type: VectorDBSearchInformedType, **kwargs: Any) -> VectorDBSearchInformedBase:
        cls = VECTOR_DB_SEARCH_INFORMED_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No informed search class registered for type '{type}'. "
                f"Known types: {list(VECTOR_DB_SEARCH_INFORMED_REGISTRY)}"
            )

        return cls(**kwargs)
