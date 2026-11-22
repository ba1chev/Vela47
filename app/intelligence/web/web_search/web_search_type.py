from enum import Enum


class WebSearchType(str, Enum):
    """Enumerates the engines a web search can be served by. DUCKDUCKGO reads
    DuckDuckGo's HTML page and needs no key, which suits a developer's own address;
    TAVILY is an API built for servers, which a cloud address can call without being
    taken for a bot."""

    DUCKDUCKGO = "duckduckgo"
    TAVILY = "tavily"
