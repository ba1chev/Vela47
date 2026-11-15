from abc import abstractmethod
from collections.abc import Hashable

from app.intelligence.memory import VectorDBSearchBase
from app.intelligence.memory import VectorDBSearchType
from app.intelligence.memory import VectorDBSearchApproximateType


class VectorDBSearchApproximateBase(VectorDBSearchBase):
    """Abstract base for approximate nearest neighbour searches. Unlike the graph
    searches, the graph is not given: the index builds it from the vectors passed to
    add(). The goal state is a query vector, and search() returns the ids of the
    vectors nearest to it, closest first, which may miss some of the exact nearest
    ones in exchange for comparing the query with only a fraction of the vectors."""

    @property
    def search_type(self) -> VectorDBSearchType:
        return VectorDBSearchType.APPROXIMATE

    @property
    @abstractmethod
    def approximate_type(self) -> VectorDBSearchApproximateType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def add(self, node: Hashable, vector: list[float]) -> None:
        raise NotImplementedError("Must be implemented")
