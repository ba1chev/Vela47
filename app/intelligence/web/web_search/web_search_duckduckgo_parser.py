from typing import Optional
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse

from app.intelligence.web import WebSearchResult


class WebSearchDuckDuckGoParser(HTMLParser):
    """Reads the results out of DuckDuckGo's HTML endpoint: the link with class
    'result__a' opens a result and carries its title and URL, and the element with class
    'result__snippet' that follows carries its excerpt.

    Links are unwrapped before they are kept. The endpoint has at times sent results
    through its own redirect, //duckduckgo.com/l/?uddg=<url>, and that inner URL is the
    one a fetch should go to. Anything still pointing at duckduckgo.com afterwards is an
    advertisement or navigation, not a result, and is dropped."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs = True)
        self.results: list[WebSearchResult] = []
        self._title: Optional[list[str]] = None
        self._snippet: Optional[list[str]] = None
        self._url: Optional[str] = None
        self._pending: Optional[dict[str, str]] = None

    def _unwrap(self, href: str) -> Optional[str]:
        url = f"https:{href}" if href.startswith("//") else href
        parsed = urlparse(url)

        if parsed.hostname and parsed.hostname.endswith("duckduckgo.com"):
            inner = parse_qs(parsed.query).get("uddg")
            if not inner:
                return None
            url, parsed = inner[0], urlparse(inner[0])
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return None
        return url

    def _flush(self) -> None:
        if self._pending is not None:
            self.results.append(WebSearchResult(**self._pending))
            self._pending = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()

        if tag == "a" and "result__a" in classes:
            self._flush()
            self._url = self._unwrap(attributes.get("href") or "")
            self._title = []
        elif "result__snippet" in classes and self._pending is not None:
            self._snippet = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._title is not None:
            title = " ".join("".join(self._title).split())
            if self._url and title:
                self._pending = {"title": title, "url": self._url, "snippet": ""}
            self._title = None
        elif self._snippet is not None and tag in ("a", "div", "td"):
            if self._pending is not None:
                self._pending["snippet"] = " ".join("".join(self._snippet).split())
            self._snippet = None
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._title is not None:
            self._title.append(data)
        elif self._snippet is not None:
            self._snippet.append(data)

    def close(self) -> None:
        super().close()
        self._flush()
