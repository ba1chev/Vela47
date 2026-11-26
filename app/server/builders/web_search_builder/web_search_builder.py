import logging

from app.server.config import Config
from app.intelligence.web import WebFetcher
from app.intelligence.web import WebSearchType
from app.intelligence.web import WebSearchBase
from app.intelligence.web import WebSearchFactory
from app.server.config_platform import ConfigPlatform

WEB_SEARCH_TYPES = {
    ConfigPlatform.LOCAL: WebSearchType.DUCKDUCKGO,
    ConfigPlatform.AWS: WebSearchType.TAVILY
}

logger = logging.getLogger("vela47")


def build_web_search(config: Config, web_fetcher: WebFetcher) -> WebSearchBase:
    search_type = WEB_SEARCH_TYPES[config.platform]
    if search_type is WebSearchType.TAVILY:
        if config.tavily_api_key is not None:
            return WebSearchFactory().create(search_type, api_key = config.tavily_api_key.get_secret_value())
        logger.warning(
            "No Tavily API key is configured, so the web search falls back to DuckDuckGo, "
            "which blocks most searches from a cloud address."
        )
    return WebSearchFactory().create(WebSearchType.DUCKDUCKGO, web_fetcher = web_fetcher)
