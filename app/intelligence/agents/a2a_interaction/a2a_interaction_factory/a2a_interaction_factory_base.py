from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.agents import A2AInteractionType
from app.intelligence.agents import A2AInteractionBase


class A2AInteractionFactoryBase(ABC):
    """Abstract factory for A2AInteractionBase instances. Lets the subagents layer ask
    for an interaction by type — the type the sandbox it runs on calls for — without
    importing the concrete interactions."""

    @abstractmethod
    def create(self, type: A2AInteractionType, **kwargs: Any) -> A2AInteractionBase:
        raise NotImplementedError("Must be implemented")
