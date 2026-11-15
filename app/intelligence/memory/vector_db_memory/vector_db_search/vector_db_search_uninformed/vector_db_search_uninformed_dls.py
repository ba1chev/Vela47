from collections.abc import Hashable

from app.intelligence.memory import VectorDBSearchUninformedBase
from app.intelligence.memory import VectorDBSearchUninformedType


class VectorDBSearchUninformedDLS(VectorDBSearchUninformedBase):
    """Depth-limited search over an unweighted graph: depth-first search that stops
    descending at a depth of tolerance edges. A node is expanded again only when it is
    reached at a smaller depth than before, because the shallower visit has more depth
    left below it. Answers only whether the goal is reachable within the limit."""

    def __init__(self, graph: dict[Hashable, set[Hashable]], tolerance: int) -> None:
        self._graph = graph
        self._tolerance = tolerance

    @property
    def uninformed_type(self) -> VectorDBSearchUninformedType:
        return VectorDBSearchUninformedType.DEPTH_LIMITED_SEARCH

    def search(self, start_state: Hashable, goal_state: Hashable) -> bool:
        return self._dls({}, start_state, goal_state, 0)

    def _dls(self, best_distance: dict[Hashable, int], current_node: Hashable,
        goal_node: Hashable, counter: int) -> bool:
        if current_node == goal_node:
            return True
        if counter == self._tolerance:
            return False

        current_best_distance = best_distance.get(current_node)
        if current_best_distance is not None and current_best_distance <= counter:
            return False

        best_distance[current_node] = counter
        for current_child_node in self._graph.get(current_node, set()):
            if self._dls(best_distance, current_child_node, goal_node, counter + 1):
                return True

        return False
