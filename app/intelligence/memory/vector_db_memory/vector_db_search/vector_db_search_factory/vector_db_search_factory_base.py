from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.memory import VectorDBSearchBase
from app.intelligence.memory import VectorDBSearchType
from app.intelligence.memory import VectorDBSearchInformedType
from app.intelligence.memory import VectorDBSearchUninformedType
from app.intelligence.memory import VectorDBSearchApproximateType


class VectorDBSearchFactoryBase(ABC):
    """Abstract factory over the three families of search. create() takes the family
    and the algorithm within it, so a caller can pick any search from two values
    without knowing which family factory builds it."""

    @abstractmethod
    def create(self, type: VectorDBSearchType,
        algorithm: VectorDBSearchUninformedType | VectorDBSearchInformedType
            | VectorDBSearchApproximateType,
        **kwargs: Any) -> VectorDBSearchBase:
        raise NotImplementedError("Must be implemented")
