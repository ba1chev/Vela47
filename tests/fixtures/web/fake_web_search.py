from app.intelligence.web import WebSearchBase


class FakeWebSearch(WebSearchBase):
    """Returns scripted results instead of searching, and records every query, so the web
    search tool can be tested for how it presents results without DuckDuckGo."""

    def __init__(self, results = None) -> None:
        self._results = list(results or [])
        self.queries = []

    def search(self, query, max_results = 8):
        self.queries.append((query, max_results))
        return self._results[:max_results]
