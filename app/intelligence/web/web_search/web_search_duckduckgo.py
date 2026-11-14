import math
from typing import Optional

from app.intelligence.web import WebFetcher
from app.intelligence.web import WebSearchBase
from app.intelligence.web import WebAccessError
from app.intelligence.web import WebSearchResult
from app.intelligence.web import WebSearchThrottle
from app.intelligence.web import WebSearchDuckDuckGoParser


class WebSearchDuckDuckGo(WebSearchBase):
    """Searches the web through DuckDuckGo's HTML endpoint, which needs no API key or
    account. The request goes through the WebFetcher and inherits its guard, size limit
    and deadline. kl='wt-wt' asks for no region.

    DuckDuckGo answers a busy address, a cloud address above all, with a challenge page.
    Searches are paced by one WebSearchThrottle per process; a challenge is tried once
    more after a pause, and a second one pauses searching for a while. Either way it is
    an error, not an empty search, which would make the agent conclude the topic does
    not exist, and the error tells the agent to work with the pages it already has."""

    SEARCH_URL = "https://html.duckduckgo.com/html/"
    CHALLENGE_MARKERS = (b"anomaly-modal", b"challenge-form", b"anomaly.js")
    RETRY_AFTER_SECONDS = 4.0
    SHARED_THROTTLE = WebSearchThrottle()

    def __init__(self, web_fetcher: WebFetcher, region: str = "wt-wt",
        throttle: Optional[WebSearchThrottle] = None) -> None:
        self._web_fetcher: WebFetcher = web_fetcher
        self._region: str = region
        self._throttle: WebSearchThrottle = throttle if throttle is not None else self.SHARED_THROTTLE

    def _paused(self, seconds: float) -> WebAccessError:
        return WebAccessError(
            f"DuckDuckGo is limiting searches from this server, so searching is paused for "
            f"{math.ceil(seconds)}s. Do not search again now: open the pages you already found "
            f"with fetch_url, or write your report from what you have."
        )

    def _results(self, query: str) -> Optional[list[WebSearchResult]]:
        self._throttle.wait_turn()
        page = self._web_fetcher.fetch(self.SEARCH_URL, form = {"q": query, "kl": self._region})

        parser = WebSearchDuckDuckGoParser()
        parser.feed(page.content.decode(page.encoding or "utf-8", errors = "replace"))
        parser.close()

        if not parser.results and any(current_marker in page.content for current_marker in self.CHALLENGE_MARKERS):
            return None
        return parser.results

    def search(self, query: str, max_results: int = 8) -> list[WebSearchResult]:
        if self._throttle.blocked_for() > 0:
            raise self._paused(self._throttle.blocked_for())

        results = self._results(query)
        if results is None:
            self._throttle.back_off(self.RETRY_AFTER_SECONDS)
            results = self._results(query)
        if results is None:
            self._throttle.cool_down()
            raise self._paused(self._throttle.blocked_for())

        unique: dict[str, WebSearchResult] = {}
        for current_result in results:
            unique.setdefault(current_result.url, current_result)
        return list(unique.values())[:max_results]
