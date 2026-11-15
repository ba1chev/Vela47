from app.intelligence.memory import VectorDBSearchType
from app.intelligence.memory import VectorDBSearchInformedFactory
from app.intelligence.memory import VectorDBSearchUninformedFactory
from app.intelligence.memory import VectorDBSearchInformedFactoryBase
from app.intelligence.memory import VectorDBSearchUninformedFactoryBase


VECTOR_DB_SEARCH_REGISTRY: dict[VectorDBSearchType,
    type[VectorDBSearchUninformedFactoryBase] | type[VectorDBSearchInformedFactoryBase]] = {
    VectorDBSearchType.UNINFORMED: VectorDBSearchUninformedFactory,
    VectorDBSearchType.INFORMED: VectorDBSearchInformedFactory
}
