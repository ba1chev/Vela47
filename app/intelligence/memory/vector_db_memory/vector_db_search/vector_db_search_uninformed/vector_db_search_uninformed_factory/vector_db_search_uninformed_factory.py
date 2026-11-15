from typing import Any

from app.intelligence.memory import VectorDBSearchUninformedBase
from app.intelligence.memory import VectorDBSearchUninformedType
from app.intelligence.memory import VectorDBSearchUninformedFactoryBase
from app.intelligence.memory import VECTOR_DB_SEARCH_UNINFORMED_REGISTRY


class VectorDBSearchUninformedFactory(VectorDBSearchUninformedFactoryBase):
    """Concrete factory that maps each VectorDBSearchUninformedType to its class
    through VECTOR_DB_SEARCH_UNINFORMED_REGISTRY. Keyword arguments are forwarded
    verbatim, so callers supply the graph and any algorithm-specific parameter, such
    as DEPTH_LIMITED_SEARCH's tolerance, without the factory knowing about them."""

    def create(self, type: VectorDBSearchUninformedType, **kwargs: Any) -> VectorDBSearchUninformedBase:
        cls = VECTOR_DB_SEARCH_UNINFORMED_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No uninformed search class registered for type '{type}'. "
                f"Known types: {list(VECTOR_DB_SEARCH_UNINFORMED_REGISTRY)}"
            )

        return cls(**kwargs)
