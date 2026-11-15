from app.intelligence.memory import VectorDBSearchType
from app.intelligence.memory import VectorDBSearchInformedFactory
from app.intelligence.memory import VectorDBSearchUninformedFactory
from app.intelligence.memory import VectorDBSearchApproximateFactory
from app.intelligence.memory import VectorDBSearchInformedFactoryBase
from app.intelligence.memory import VectorDBSearchUninformedFactoryBase
from app.intelligence.memory import VectorDBSearchApproximateFactoryBase


VECTOR_DB_SEARCH_REGISTRY: dict[VectorDBSearchType,
    type[VectorDBSearchUninformedFactoryBase] | type[VectorDBSearchInformedFactoryBase]
    | type[VectorDBSearchApproximateFactoryBase]] = {
    VectorDBSearchType.UNINFORMED: VectorDBSearchUninformedFactory,
    VectorDBSearchType.INFORMED: VectorDBSearchInformedFactory,
    VectorDBSearchType.APPROXIMATE: VectorDBSearchApproximateFactory
}
