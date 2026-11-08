from abc import ABC, abstractmethod

from app.intelligence.web import WebSearchResult


class WebSearchBase(ABC):
    """Abstract base for a web search backend. A search turns a query into a short list of
    pages worth reading; reading them is the WebFetcher's job, so a backend stays a thin
    adapter over one engine and can be swapped for another — a paid API with a key, a
    self-hosted SearXNG — without the tool that calls it changing."""

    @abstractmethod
    def search(self, query: str, max_results: int = 8) -> list[WebSearchResult]:
        raise NotImplementedError("Must be implemented")
