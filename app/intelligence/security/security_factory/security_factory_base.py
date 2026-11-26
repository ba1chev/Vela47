from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.security import SecurityBase
from app.intelligence.security import SecurityType
from app.intelligence.security import SecurityPromptType


class SecurityFactoryBase(ABC):
    """Abstract factory over the families of threat. create() takes the family and the
    threat within it, so a caller can have any detector built from two values without
    knowing which family factory builds it."""

    @abstractmethod
    def create(self, type: SecurityType, threat: SecurityPromptType, **kwargs: Any) -> SecurityBase:
        raise NotImplementedError("Must be implemented")
