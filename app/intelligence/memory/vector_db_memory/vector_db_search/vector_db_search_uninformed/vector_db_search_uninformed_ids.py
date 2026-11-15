from collections.abc import Hashable

from app.intelligence.memory import VectorDBSearchUninformedDLS
from app.intelligence.memory import VectorDBSearchUninformedBase
from app.intelligence.memory import VectorDBSearchUninformedType


class VectorDBSearchUninformedIDS(VectorDBSearchUninformedBase):
    """Iterative deepening search over an unweighted graph: depth-limited search run
    with a limit of 0, 1, 2 and so on, below upper_bound, until one run reaches the
    goal. It finds the shallowest goal like breadth-first search while keeping only
    one path in memory like depth-first search."""

    def __init__(self, graph: dict[Hashable, set[Hashable]], upper_bound: int) -> None:
        self._graph = graph
        self._upper_bound = upper_bound

    @property
    def uninformed_type(self) -> VectorDBSearchUninformedType:
        return VectorDBSearchUninformedType.ITERATIVE_DEEPENING_SEARCH

    def search(self, start_state: Hashable, goal_state: Hashable) -> bool:
        for tolerance in range(self._upper_bound):
            if VectorDBSearchUninformedDLS(self._graph, tolerance).search(start_state, goal_state):
                return True
        return False
