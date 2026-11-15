from collections import deque
from collections.abc import Hashable

from app.intelligence.memory import VectorDBSearchUninformedBase
from app.intelligence.memory import VectorDBSearchUninformedType


class VectorDBSearchUninformedBFS(VectorDBSearchUninformedBase):
    """Breadth-first search over an unweighted graph. Expands nodes level by level, so
    it reaches the goal through the fewest edges, and answers only whether the goal is
    reachable from the start. A node is marked visited when it is queued, not when it
    is expanded, so it never enters the queue twice."""

    def __init__(self, graph: dict[Hashable, set[Hashable]]) -> None:
        self._graph = graph

    @property
    def uninformed_type(self) -> VectorDBSearchUninformedType:
        return VectorDBSearchUninformedType.BREADTH_FIRST_SEARCH

    def search(self, start_state: Hashable, goal_state: Hashable) -> bool:
        if start_state == goal_state:
            return True

        queue: deque[Hashable] = deque()
        visited: set[Hashable] = set()

        queue.append(start_state)
        visited.add(start_state)
        while queue:
            current_node = queue.popleft()
            if current_node == goal_state:
                return True

            for current_child_node in self._graph.get(current_node, set()):
                if current_child_node not in visited:
                    queue.append(current_child_node)
                    visited.add(current_child_node)

        return False
