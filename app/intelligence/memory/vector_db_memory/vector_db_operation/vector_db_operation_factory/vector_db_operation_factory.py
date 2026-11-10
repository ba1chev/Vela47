from typing import Any

from app.intelligence.memory import VectorDbOperation
from app.intelligence.memory import VectorDbOperationType
from app.intelligence.memory import VECTOR_DB_OPERATION_REGISTRY
from app.intelligence.memory import VectorDbOperationBaseFactory


class VectorDbOperationFactory(VectorDbOperationBaseFactory):
    """Concrete factory that maps each VectorDbOperationType to its VectorDbOperation
    subclass through VECTOR_DB_OPERATION_REGISTRY and delegates construction to it.
    Additional keyword arguments are forwarded verbatim, so callers can supply
    operation-specific parameters, such as SEARCH's top_k or DEDUPLICATE's threshold,
    without the factory knowing about them."""

    def create(self, type: VectorDbOperationType, **kwargs: Any) -> VectorDbOperation:
        cls = VECTOR_DB_OPERATION_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No operation class registered for type '{type}'. "
                f"Known types: {list(VECTOR_DB_OPERATION_REGISTRY)}"
            )

        return cls(**kwargs)
