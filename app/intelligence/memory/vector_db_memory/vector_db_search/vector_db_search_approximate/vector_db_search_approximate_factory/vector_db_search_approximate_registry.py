from app.intelligence.memory import VectorDBSearchApproximateBase
from app.intelligence.memory import VectorDBSearchApproximateHNSW
from app.intelligence.memory import VectorDBSearchApproximateType


VECTOR_DB_SEARCH_APPROXIMATE_REGISTRY: dict[VectorDBSearchApproximateType,
    type[VectorDBSearchApproximateBase]] = {
    VectorDBSearchApproximateType.HIERARCHICAL_NAVIGABLE_SMALL_WORLD: VectorDBSearchApproximateHNSW
}
