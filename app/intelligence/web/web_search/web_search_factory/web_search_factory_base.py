from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.web import WebSearchType
from app.intelligence.web import WebSearchBase


class WebSearchFactoryBase(ABC):
    """Abstract factory for WebSearchBase instances. Lets the server pick the search
    engine of its environment by type without importing the concrete backends."""

    @abstractmethod
    def create(self, type: WebSearchType, **kwargs: Any) -> WebSearchBase:
        raise NotImplementedError("Must be implemented")
