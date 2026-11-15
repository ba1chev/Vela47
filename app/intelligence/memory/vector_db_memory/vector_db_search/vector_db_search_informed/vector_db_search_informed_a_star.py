from math import inf
from itertools import count
from typing import Callable
from heapq import heappop, heappush
from collections.abc import Hashable

from app.intelligence.memory import reconstruct_path
from app.intelligence.memory import VectorDBSearchEdge
from app.intelligence.memory import VectorDBSearchInformedBase
from app.intelligence.memory import VectorDBSearchInformedType


class VectorDBSearchInformedAStar(VectorDBSearchInformedBase):
    """A* search over a weighted graph. Expands the node with the lowest path cost plus
    heuristic and keeps only the cheapest known path to every node, so with a heuristic
    that never overestimates, the path it returns is the cheapest one. Returns the path
    from start to goal, or an empty list when the goal is unreachable."""

    def __init__(self, graph: dict[Hashable, list[VectorDBSearchEdge]],
        heuristics: Callable[[Hashable], float]) -> None:
        self._graph = graph
        self._heuristics = heuristics

    @property
    def informed_type(self) -> VectorDBSearchInformedType:
        return VectorDBSearchInformedType.A_STAR_SEARCH

    def search(self, start_state: Hashable, goal_state: Hashable) -> list[Hashable]:
        if start_state == goal_state:
            return [start_state]

        sequence = count()
        queue: list[tuple[float, int, Hashable, float]] = []
        visited: set[Hashable] = set()
        parents: dict[Hashable, Hashable] = {}
        distances: dict[Hashable, float] = {}

        distances[start_state] = 0
        heappush(queue, (self._heuristics(start_state), next(sequence), start_state, 0))
        while queue:
            _, _, current_node, current_distance = heappop(queue)

            if current_node in visited:
                continue
            visited.add(current_node)

            if current_node == goal_state:
                return reconstruct_path(parents, goal_state)

            for current_child_node in self._graph.get(current_node, []):
                if current_child_node.to in visited:
                    continue

                child_distance = current_distance + current_child_node.weight
                if child_distance < distances.get(current_child_node.to, inf):
                    parents[current_child_node.to] = current_node
                    distances[current_child_node.to] = child_distance
                    child_priority = child_distance + self._heuristics(current_child_node.to)
                    heappush(queue, (child_priority, next(sequence),
                        current_child_node.to, child_distance))

        return []
