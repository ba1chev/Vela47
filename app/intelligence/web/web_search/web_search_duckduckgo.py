from app.intelligence.web import WebFetcher
from app.intelligence.web import WebSearchBase
from app.intelligence.web import WebAccessError
from app.intelligence.web import WebSearchResult
from app.intelligence.web import WebSearchDuckDuckGoParser


class WebSearchDuckDuckGo(WebSearchBase):
    """Searches the web through DuckDuckGo's HTML endpoint, which needs no API key or
    account, so a local deployment can search at all. The request goes through the
    WebFetcher and inherits its guard, size limit and deadline.

    A challenge page means DuckDuckGo is rate limiting this address and is reported as
    an error, not as an empty search, which would make the agent conclude the topic does
    not exist. kl='wt-wt' asks for no region."""

    SEARCH_URL = "https://html.duckduckgo.com/html/"
    CHALLENGE_MARKERS = (b"anomaly-modal", b"challenge-form", b"anomaly.js")

    def __init__(self, web_fetcher: WebFetcher, region: str = "wt-wt") -> None:
        self._web_fetcher: WebFetcher = web_fetcher
        self._region: str = region

    def search(self, query: str, max_results: int = 8) -> list[WebSearchResult]:
        page = self._web_fetcher.fetch(self.SEARCH_URL, form = {"q": query, "kl": self._region})

        parser = WebSearchDuckDuckGoParser()
        parser.feed(page.content.decode(page.encoding or "utf-8", errors = "replace"))
        parser.close()

        if not parser.results and any(current_marker in page.content for current_marker in self.CHALLENGE_MARKERS):
            raise WebAccessError(
                "DuckDuckGo answered with a challenge instead of results — searching is rate "
                "limited for now. Work from what you already have."
            )

        unique: dict[str, WebSearchResult] = {}
        for current_result in parser.results:
            unique.setdefault(current_result.url, current_result)
        return list(unique.values())[:max_results]
