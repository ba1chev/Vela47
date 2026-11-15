from abc import abstractmethod

from app.intelligence.memory import VectorDBSearchBase
from app.intelligence.memory import VectorDBSearchType
from app.intelligence.memory import VectorDBSearchInformedType


class VectorDBSearchInformedBase(VectorDBSearchBase):
    """Abstract base for the searches steered by a heuristic: a function that estimates
    the remaining cost from a node to the goal. The heuristic is given at construction;
    how well it estimates decides how directly the search heads for the goal and, for
    A* and IDA*, whether the path it returns is the cheapest one."""

    @property
    def search_type(self) -> VectorDBSearchType:
        return VectorDBSearchType.INFORMED

    @property
    @abstractmethod
    def informed_type(self) -> VectorDBSearchInformedType:
        raise NotImplementedError("Must be implemented")
