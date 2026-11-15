from math import inf
from itertools import count
from heapq import heappop, heappush
from collections.abc import Hashable

from app.intelligence.memory import reconstruct_path
from app.intelligence.memory import VectorDBSearchEdge
from app.intelligence.memory import VectorDBSearchUninformedBase
from app.intelligence.memory import VectorDBSearchUninformedType


class VectorDBSearchUninformedUCS(VectorDBSearchUninformedBase):
    """Uniform cost search over a weighted graph. Always expands the node with the
    cheapest path found so far, so the first time the goal is expanded its path is the
    cheapest one. Returns that path from start to goal, or an empty list when the goal
    is unreachable. Ties in cost are expanded in the order they were queued."""

    def __init__(self, graph: dict[Hashable, list[VectorDBSearchEdge]]) -> None:
        self._graph = graph

    @property
    def uninformed_type(self) -> VectorDBSearchUninformedType:
        return VectorDBSearchUninformedType.UNIFORM_COST_SEARCH

    def search(self, start_state: Hashable, goal_state: Hashable) -> list[Hashable]:
        sequence = count()
        queue: list[tuple[float, int, Hashable]] = []
        visited: set[Hashable] = set()
        parents: dict[Hashable, Hashable] = {}
        distances: dict[Hashable, float] = {}

        distances[start_state] = 0
        heappush(queue, (0, next(sequence), start_state))
        while queue:
            current_distance, _, current_node = heappop(queue)

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
                    heappush(queue, (child_distance, next(sequence), current_child_node.to))
                    distances[current_child_node.to] = child_distance
                    parents[current_child_node.to] = current_node

        return []
