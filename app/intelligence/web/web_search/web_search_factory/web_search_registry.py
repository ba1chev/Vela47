from app.intelligence.web import WebSearchType
from app.intelligence.web import WebSearchBase
from app.intelligence.web import WebSearchTavily
from app.intelligence.web import WebSearchDuckDuckGo


WEB_SEARCH_REGISTRY: dict[WebSearchType, type[WebSearchBase]] = {
    WebSearchType.DUCKDUCKGO: WebSearchDuckDuckGo,
    WebSearchType.TAVILY: WebSearchTavily
}
