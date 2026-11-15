from app.intelligence.memory import VectorDBSearchUninformedBFS
from app.intelligence.memory import VectorDBSearchUninformedDFS
from app.intelligence.memory import VectorDBSearchUninformedDLS
from app.intelligence.memory import VectorDBSearchUninformedIDS
from app.intelligence.memory import VectorDBSearchUninformedUCS
from app.intelligence.memory import VectorDBSearchUninformedBase
from app.intelligence.memory import VectorDBSearchUninformedType


VECTOR_DB_SEARCH_UNINFORMED_REGISTRY: dict[VectorDBSearchUninformedType,
    type[VectorDBSearchUninformedBase]] = {
    VectorDBSearchUninformedType.DEPTH_FIRST_SEARCH: VectorDBSearchUninformedDFS,
    VectorDBSearchUninformedType.BREADTH_FIRST_SEARCH: VectorDBSearchUninformedBFS,
    VectorDBSearchUninformedType.UNIFORM_COST_SEARCH: VectorDBSearchUninformedUCS,
    VectorDBSearchUninformedType.DEPTH_LIMITED_SEARCH: VectorDBSearchUninformedDLS,
    VectorDBSearchUninformedType.ITERATIVE_DEEPENING_SEARCH: VectorDBSearchUninformedIDS
}
