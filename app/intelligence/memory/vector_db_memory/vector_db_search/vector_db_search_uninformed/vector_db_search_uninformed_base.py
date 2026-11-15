from abc import abstractmethod

from app.intelligence.memory import VectorDBSearchBase
from app.intelligence.memory import VectorDBSearchType
from app.intelligence.memory import VectorDBSearchUninformedType


class VectorDBSearchUninformedBase(VectorDBSearchBase):
    """Abstract base for the searches that use no knowledge of where the goal lies.
    They tell nodes apart only by how they were reached (order, depth or path cost),
    and recognise the goal by equality when they reach it."""

    @property
    def search_type(self) -> VectorDBSearchType:
        return VectorDBSearchType.UNINFORMED

    @property
    @abstractmethod
    def uninformed_type(self) -> VectorDBSearchUninformedType:
        raise NotImplementedError("Must be implemented")
