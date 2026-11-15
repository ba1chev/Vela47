from itertools import count
from typing import Callable
from collections.abc import Hashable
from heapq import heapify, heappop, heappush, nsmallest

from app.intelligence.memory import reconstruct_path
from app.intelligence.memory import VectorDBSearchEdge
from app.intelligence.memory import VectorDBSearchInformedBase
from app.intelligence.memory import VectorDBSearchInformedType


class VectorDBSearchInformedBeam(VectorDBSearchInformedBase):
    """Beam search over a weighted graph: greedy best-first search whose queue is cut
    back to the queue_limit nodes the heuristic rates best after every expansion.
    Memory stays bounded, but a node cut from the beam is never reconsidered, so the
    goal can be missed even when it is reachable. Returns the path, or an empty list."""

    def __init__(self, graph: dict[Hashable, list[VectorDBSearchEdge]], queue_limit: int,
        heuristics: Callable[[Hashable], float]) -> None:
        self._graph = graph
        self._queue_limit = queue_limit
        self._heuristics = heuristics

    @property
    def informed_type(self) -> VectorDBSearchInformedType:
        return VectorDBSearchInformedType.BEAM_SEARCH

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

            if current_node in visited:
                continue
            visited.add(current_node)

            if current_node == goal_state:
                return reconstruct_path(parents, goal_state)

            for current_child_node in self._graph.get(current_node, []):
                if current_child_node.to in visited:
                    continue

                parents[current_child_node.to] = current_node
                child_distance = current_distance + current_child_node.weight
                heappush(queue, (self._heuristics(current_child_node.to), next(sequence),
                    current_child_node.to, child_distance))

            if len(queue) > self._queue_limit:
                queue = nsmallest(self._queue_limit, queue)
                heapify(queue)

        return []
