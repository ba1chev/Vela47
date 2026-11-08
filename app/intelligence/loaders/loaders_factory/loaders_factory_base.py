from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.loaders import LoaderBase
from app.intelligence.loaders import LoaderType


class LoadersFactoryBase(ABC):
    """Abstract factory for LoaderBase instances. Lets the code that ingests uploads and
    the tool that reads web pages ask for a loader by type — the form resolve_loader_type
    answers in — without importing the concrete loaders."""

    @abstractmethod
    def create(self, type: LoaderType, **kwargs: Any) -> LoaderBase:
        raise NotImplementedError("Must be implemented")
