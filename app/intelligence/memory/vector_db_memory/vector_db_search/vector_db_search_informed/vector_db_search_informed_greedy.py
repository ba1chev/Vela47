from itertools import count
from typing import Callable
from heapq import heappop, heappush
from collections.abc import Hashable

from app.intelligence.memory import reconstruct_path
from app.intelligence.memory import VectorDBSearchEdge
from app.intelligence.memory import VectorDBSearchInformedBase
from app.intelligence.memory import VectorDBSearchInformedType


class VectorDBSearchInformedGreedy(VectorDBSearchInformedBase):
    """Greedy best-first search over a weighted graph. Expands the node the heuristic
    rates closest to the goal and ignores what the path cost so far, so it is fast but
    the path it returns need not be the cheapest. A node's parent is the last node that
    queued it. Returns the path, or an empty list when the goal is unreachable."""

    def __init__(self, graph: dict[Hashable, list[VectorDBSearchEdge]],
        heuristics: Callable[[Hashable], float]) -> None:
        self._graph = graph
        self._heuristics = heuristics

    @property
    def informed_type(self) -> VectorDBSearchInformedType:
        return VectorDBSearchInformedType.GREEDY_SEARCH

    def search(self, start_state: Hashable, goal_state: Hashable) -> list[Hashable]:
        if start_state == goal_state:
            return [start_state]

        sequence = count()
        queue: list[tuple[float, int, Hashable, float]] = []
        visited: set[Hashable] = set()
        parents: dict[Hashable, Hashable] = {}

        heappush(queue, (self._heuristics(start_state), next(sequence), start_state, 0))
        while queue:
            _, _, current_node, current_distance = heappop(queue)

            if current_node == goal_state:
                return reconstruct_path(parents, goal_state)

            if current_node in visited:
                continue
            visited.add(current_node)

            for current_child_node in self._graph.get(current_node, []):
                if current_child_node.to in visited:
                    continue

                parents[current_child_node.to] = current_node
                child_distance = current_distance + current_child_node.weight
                heappush(queue, (self._heuristics(current_child_node.to), next(sequence),
                    current_child_node.to, child_distance))

        return []
