from app.intelligence.memory import VectorDBSearchInformedBeam
from app.intelligence.memory import VectorDBSearchInformedBase
from app.intelligence.memory import VectorDBSearchInformedType
from app.intelligence.memory import VectorDBSearchInformedAStar
from app.intelligence.memory import VectorDBSearchInformedGreedy
from app.intelligence.memory import VectorDBSearchInformedIDAStar
from app.intelligence.memory import VectorDBSearchInformedHillClimbing


VECTOR_DB_SEARCH_INFORMED_REGISTRY: dict[VectorDBSearchInformedType,
    type[VectorDBSearchInformedBase]] = {
    VectorDBSearchInformedType.A_STAR_SEARCH: VectorDBSearchInformedAStar,
    VectorDBSearchInformedType.BEAM_SEARCH: VectorDBSearchInformedBeam,
    VectorDBSearchInformedType.GREEDY_SEARCH: VectorDBSearchInformedGreedy,
    VectorDBSearchInformedType.HILL_CLIMBING: VectorDBSearchInformedHillClimbing,
    VectorDBSearchInformedType.ITERATIVE_DEEPENING_A_STAR_SEARCH: VectorDBSearchInformedIDAStar
}
