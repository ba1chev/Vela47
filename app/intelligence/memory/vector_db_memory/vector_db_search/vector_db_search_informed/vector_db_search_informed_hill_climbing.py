from typing import Callable
from collections.abc import Hashable

from app.intelligence.memory import VectorDBSearchEdge
from app.intelligence.memory import VectorDBSearchInformedBeam
from app.intelligence.memory import VectorDBSearchInformedBase
from app.intelligence.memory import VectorDBSearchInformedType


class VectorDBSearchInformedHillClimbing(VectorDBSearchInformedBase):
    """Hill climbing over a weighted graph: beam search with a beam of one, so after
    every expansion only the neighbour the heuristic rates best is kept. It never
    backtracks, which makes it stop at a local optimum or a dead end and return an
    empty list even when the goal is reachable."""

    def __init__(self, graph: dict[Hashable, list[VectorDBSearchEdge]],
        heuristics: Callable[[Hashable], float]) -> None:
        self._graph = graph
        self._heuristics = heuristics

    @property
    def informed_type(self) -> VectorDBSearchInformedType:
        return VectorDBSearchInformedType.HILL_CLIMBING

    def search(self, start_state: Hashable, goal_state: Hashable) -> list[Hashable]:
        return VectorDBSearchInformedBeam(
            self._graph, 1, self._heuristics
        ).search(start_state, goal_state)
