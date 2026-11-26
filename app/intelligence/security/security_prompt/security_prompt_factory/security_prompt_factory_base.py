from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.security import SecurityPrompt
from app.intelligence.security import SecurityPromptType


class SecurityPromptFactoryBase(ABC):
    """Abstract factory for SecurityPrompt instances. Lets SecurityFactory, and whatever
    watches one kind of text, ask for the detector of a prompt threat by type without
    importing the concrete detectors."""

    @abstractmethod
    def create(self, type: SecurityPromptType, **kwargs: Any) -> SecurityPrompt:
        raise NotImplementedError("Must be implemented")
