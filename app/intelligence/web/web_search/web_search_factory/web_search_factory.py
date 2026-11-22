from typing import Any

from app.intelligence.web import WebSearchType
from app.intelligence.web import WebSearchBase
from app.intelligence.web import WEB_SEARCH_REGISTRY
from app.intelligence.web import WebSearchFactoryBase


class WebSearchFactory(WebSearchFactoryBase):
    """Concrete factory that maps each WebSearchType to its WebSearchBase subclass and
    forwards the keyword arguments to it. A backend holds no conversation, so one per
    process serves every run.

    Registry reference:
      DUCKDUCKGO -> WebSearchDuckDuckGo(web_fetcher=<WebFetcher>)
      TAVILY     -> WebSearchTavily(api_key=<key>)"""

    def create(self, type: WebSearchType, **kwargs: Any) -> WebSearchBase:
        cls = WEB_SEARCH_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No web search class registered for type '{type}'. "
                f"Known types: {list(WEB_SEARCH_REGISTRY)}"
            )

        return cls(**kwargs)
