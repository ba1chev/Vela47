from typing import Any

from app.intelligence.memory import VectorDBSearchBase
from app.intelligence.memory import VectorDBSearchType
from app.intelligence.memory import VECTOR_DB_SEARCH_REGISTRY
from app.intelligence.memory import VectorDBSearchFactoryBase
from app.intelligence.memory import VectorDBSearchInformedType
from app.intelligence.memory import VectorDBSearchUninformedType


class VectorDBSearchFactory(VectorDBSearchFactoryBase):
    """Concrete factory that picks the family factory for a VectorDBSearchType through
    VECTOR_DB_SEARCH_REGISTRY and lets it build the algorithm. An algorithm of the
    other family is not in that factory's registry, so the mismatch is reported by the
    family factory's ValueError."""

    def create(self, type: VectorDBSearchType,
        algorithm: VectorDBSearchUninformedType | VectorDBSearchInformedType,
        **kwargs: Any) -> VectorDBSearchBase:
        factory = VECTOR_DB_SEARCH_REGISTRY.get(type)

        if factory is None:
            raise ValueError(
                f"No search factory registered for type '{type}'. "
                f"Known types: {list(VECTOR_DB_SEARCH_REGISTRY)}"
            )

        return factory().create(algorithm, **kwargs)
