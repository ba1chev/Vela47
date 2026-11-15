from collections.abc import Hashable

from app.intelligence.memory import VectorDBSearchUninformedBase
from app.intelligence.memory import VectorDBSearchUninformedType


class VectorDBSearchUninformedDFS(VectorDBSearchUninformedBase):
    """Depth-first search over an unweighted graph. Follows one branch as deep as it
    goes before backtracking, expands every node at most once, and answers only
    whether the goal is reachable from the start. The visited set is created by
    each search() call, so searches on one instance are independent."""

    def __init__(self, graph: dict[Hashable, set[Hashable]]) -> None:
        self._graph = graph

    @property
    def uninformed_type(self) -> VectorDBSearchUninformedType:
        return VectorDBSearchUninformedType.DEPTH_FIRST_SEARCH

    def search(self, start_state: Hashable, goal_state: Hashable) -> bool:
        return self._dfs(set(), start_state, goal_state)

    def _dfs(self, visited: set[Hashable], current_node: Hashable, goal_node: Hashable) -> bool:
        if current_node == goal_node:
            return True
        if current_node in visited:
            return False

        visited.add(current_node)
        for current_child_node in self._graph.get(current_node, set()):
            if current_child_node not in visited:
                if self._dfs(visited, current_child_node, goal_node):
                    return True
        return False
