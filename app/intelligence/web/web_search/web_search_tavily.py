import httpx
from typing import Any, Optional

from app.intelligence.web import WebSearchBase
from app.intelligence.web import WebAccessError
from app.intelligence.web import WebSearchResult


class WebSearchTavily(WebSearchBase):
    """Searches the web through Tavily's search API, which is meant to be called from
    servers: a cloud address that DuckDuckGo answers with a challenge page gets results
    here. Each search is one basic search, one API credit, with no generated answer and
    no page content, since pages are read through fetch_url.

    The host is fixed and known, so the request goes straight to it rather than through
    the WebFetcher's guard, and proxies in the environment are ignored as they are there.
    A refused key, a spent quota or an unreachable API is an error, never an empty
    search, and it tells the agent to work with the pages it already has."""

    SEARCH_URL = "https://api.tavily.com/search"
    MAX_RESULTS = 20
    LIMIT_STATUSES = (429, 432, 433)

    def __init__(self, api_key: str, timeout_seconds: float = 15.0,
        transport: Optional[httpx.BaseTransport] = None) -> None:
        self._api_key: str = api_key
        self._timeout_seconds: float = timeout_seconds
        self._transport: Optional[httpx.BaseTransport] = transport

    def _unavailable(self, reason: str) -> WebAccessError:
        return WebAccessError(
            f"The web search is unavailable: {reason}. Do not search again now: open the pages "
            f"you already found with fetch_url, or write your report from what you have."
        )

    def _post(self, body: dict[str, Any]) -> httpx.Response:
        with httpx.Client(timeout = self._timeout_seconds, transport = self._transport, trust_env = False) as client:
            return client.post(self.SEARCH_URL, json = body, headers = {"Authorization": f"Bearer {self._api_key}"})

    def search(self, query: str, max_results: int = 8) -> list[WebSearchResult]:
        body = {
            "query": query,
            "max_results": max(1, min(max_results, self.MAX_RESULTS)),
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": False,
            "include_images": False
        }
        try:
            response = self._post(body)
        except httpx.HTTPError as e:
            raise self._unavailable(f"the search API could not be reached ({type(e).__name__})") from e

        if response.status_code == 401:
            raise self._unavailable("the search API refused this server's key")
        if response.status_code in self.LIMIT_STATUSES:
            raise self._unavailable("this server has used up its searches for now")
        if response.status_code != 200:
            raise self._unavailable(f"the search API answered with status {response.status_code}")

        try:
            items = response.json().get("results") or []
        except ValueError as e:
            raise self._unavailable("the search API sent an answer that is not JSON") from e

        unique: dict[str, WebSearchResult] = {}
        for current_item in items:
            url = str(current_item.get("url") or "").strip()
            if not url.startswith(("http://", "https://")):
                continue
            unique.setdefault(url, WebSearchResult(
                title = str(current_item.get("title") or url).strip(),
                url = url,
                snippet = " ".join(str(current_item.get("content") or "").split())
            ))
        return list(unique.values())[:max_results]
