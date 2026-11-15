from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.intelligence.memory import VectorDBSearchType

TInputState = TypeVar("TInputState")
TOutputState = TypeVar("TOutputState")
TOutputResult = TypeVar("TOutputResult")


class VectorDBSearchBase(ABC, Generic[TInputState, TOutputState, TOutputResult]):
    """Abstract base for every graph search. The graph and the algorithm's parameters
    (a depth limit, a heuristic, a beam width) are given at construction, so search()
    takes only the start and goal states and one instance can run many searches.
    What a search returns depends on the algorithm: reachability, a path or a cost."""

    @property
    @abstractmethod
    def search_type(self) -> VectorDBSearchType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def search(self, start_state: TInputState, goal_state: TOutputState) -> TOutputResult:
        raise NotImplementedError("Must be implemented")
