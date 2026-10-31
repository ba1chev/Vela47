from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TTarget = TypeVar("TTarget")


class MiddlewareBase(ABC, Generic[TTarget]):
    """Abstract base for all middleware in the system. TTarget is the component
    the middleware operates on — e.g. ContextWindow for memory-related middleware.
    Each concrete subclass encapsulates one cross-cutting concern and exposes it
    through a single process() call, keeping the agent loop unaware of which
    policy or transformation is in use."""

    @abstractmethod
    def process(self, target: TTarget) -> None:
        raise NotImplementedError("Must be implemented")
