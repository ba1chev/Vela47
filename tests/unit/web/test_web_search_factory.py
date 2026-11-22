import pytest

from app.intelligence.web import WebFetcher
from app.intelligence.web import WebSearchType
from app.intelligence.web import WebSearchTavily
from app.intelligence.web import WebSearchFactory
from app.intelligence.web import WEB_SEARCH_REGISTRY
from app.intelligence.web import WebSearchDuckDuckGo


class TestWebSearchFactory:
    def test_every_type_is_registered(self):
        assert set(WEB_SEARCH_REGISTRY) == set(WebSearchType)

    def test_duckduckgo_is_given_the_fetcher(self):
        assert isinstance(WebSearchFactory().create(WebSearchType.DUCKDUCKGO, web_fetcher = WebFetcher()), WebSearchDuckDuckGo)

    def test_tavily_is_given_its_key(self):
        assert isinstance(WebSearchFactory().create(WebSearchType.TAVILY, api_key = "tvly-key"), WebSearchTavily)

    def test_an_unknown_type_is_refused(self):
        with pytest.raises(ValueError, match = "No web search class registered"):
            WebSearchFactory().create("carrier pigeon")
