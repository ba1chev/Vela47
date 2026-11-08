from app.intelligence.web import WebFetcher
from app.intelligence.web import WebSearchBase
from app.intelligence.web import WebAccessError
from app.intelligence.web import WebSearchResult
from app.intelligence.web import WebSearchDuckDuckGoParser


class WebSearchDuckDuckGo(WebSearchBase):
    """Searches the web through DuckDuckGo's HTML endpoint — the page DuckDuckGo serves to
    browsers without JavaScript. It needs no API key and no account, which is what lets
    a local deployment search at all, and it is the same source several open-source MCP
    search servers use.

    The request goes through the WebFetcher like any other, so it inherits the address
    guard, the size limit and the deadline. A page with no results that asks for a
    challenge instead means DuckDuckGo is rate limiting this address; that is reported as
    an error rather than as an empty search, because 'nothing found' would send the agent
    off to conclude the topic does not exist.

    The kl parameter sets the region; 'wt-wt' asks for no region, so results are not
    skewed toward wherever the server happens to run."""

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
