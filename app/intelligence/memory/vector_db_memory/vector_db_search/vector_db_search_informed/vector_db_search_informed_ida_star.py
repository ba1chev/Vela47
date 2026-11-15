from math import inf
from typing import Callable
from collections.abc import Hashable

from app.intelligence.memory import VectorDBSearchEdge
from app.intelligence.memory import VectorDBSearchInformedBase
from app.intelligence.memory import VectorDBSearchInformedType


class VectorDBSearchInformedIDAStar(VectorDBSearchInformedBase):
    """Iterative deepening A* over a weighted graph: depth-first search cut off where
    path cost plus heuristic exceeds a tolerance, restarted with the smallest value that
    exceeded it until the goal is reached. Uses the memory of depth-first search and,
    with a heuristic that never overestimates, returns the cheapest path's cost, or -1
    when the goal is unreachable. It returns the cost only, not the path."""

    def __init__(self, graph: dict[Hashable, list[VectorDBSearchEdge]],
        heuristics: Callable[[Hashable], float]) -> None:
        self._graph = graph
        self._heuristics = heuristics

    @property
    def informed_type(self) -> VectorDBSearchInformedType:
        return VectorDBSearchInformedType.ITERATIVE_DEEPENING_A_STAR_SEARCH

    def search(self, start_state: Hashable, goal_state: Hashable) -> float:
        best_distance: dict[Hashable, float] = {}
        tolerance = self._heuristics(start_state)

        while True:
            best_distance.clear()
            found, next_tolerance = self._ida_star(best_distance, start_state,
                goal_state, 0, tolerance, inf)

            if found:
                return tolerance
            if next_tolerance == inf:
                return -1
            tolerance = next_tolerance

    def _ida_star(self, best_distance: dict[Hashable, float], current_node: Hashable,
        goal_node: Hashable, distance: float, tolerance: float,
        next_tolerance: float) -> tuple[bool, float]:
        current_distance = distance + self._heuristics(current_node)
        if current_distance > tolerance:
            return False, min(next_tolerance, current_distance)
        if current_node == goal_node:
            return True, next_tolerance

        current_best_distance = best_distance.get(current_node)
        if current_best_distance is not None and current_best_distance <= distance:
            return False, next_tolerance

        best_distance[current_node] = distance
        for current_child_node in self._graph.get(current_node, []):
            found, next_tolerance = self._ida_star(best_distance, current_child_node.to,
                goal_node, distance + current_child_node.weight, tolerance, next_tolerance)
            if found:
                return True, next_tolerance

        return False, next_tolerance
