import pytest

from app.intelligence.web import WebFetcher
from app.intelligence.web import WebAccessError
from app.intelligence.web import WebAddressGuard
from app.intelligence.web import WebSearchDuckDuckGo
from tests.fixtures.web.fake_resolver import FakeResolver
from app.intelligence.web import WebSearchDuckDuckGoParser
from tests.fixtures.web.fake_web_server import FakeWebServer
from tests.fixtures.web.duckduckgo_page import DUCKDUCKGO_PAGE
from tests.fixtures.web.duckduckgo_page import DUCKDUCKGO_CHALLENGE_PAGE


def make_search(page = DUCKDUCKGO_PAGE):
    server = FakeWebServer({WebSearchDuckDuckGo.SEARCH_URL: FakeWebServer.page(page)})
    fetcher = WebFetcher(WebAddressGuard(FakeResolver()), transport = server.transport)
    return WebSearchDuckDuckGo(fetcher), server


def parse(page):
    parser = WebSearchDuckDuckGoParser()
    parser.feed(page)
    parser.close()
    return parser.results


class TestWebSearchDuckDuckGo:
    def test_results_carry_title_url_and_snippet(self):
        first = parse(DUCKDUCKGO_PAGE)[0]
        assert first.title == "How to parametrize fixtures and test functions - pytest documentation"
        assert first.url == "https://docs.pytest.org/en/stable/how-to/parametrize.html"
        assert first.snippet == "pytest enables test parametrization at several levels & more."

    def test_a_redirect_link_is_unwrapped_to_its_target(self):
        assert parse(DUCKDUCKGO_PAGE)[1].url == "https://example.org/guide?a=1"
        assert parse(DUCKDUCKGO_PAGE)[1].title == "A guide to parametrize"

    def test_advertisements_are_dropped(self):
        assert all("duckduckgo.com" not in current.url for current in parse(DUCKDUCKGO_PAGE))

    def test_the_query_is_posted_with_the_region(self):
        search, server = make_search()
        search.search("pytest parametrize")
        request = server.requests[0]
        assert request.method == "POST" and request.headers["host"] == "html.duckduckgo.com"
        assert request.content == b"q=pytest+parametrize&kl=wt-wt"

    def test_repeated_pages_are_listed_once(self):
        search, _ = make_search()
        urls = [current.url for current in search.search("x")]
        assert len(urls) == len(set(urls)) == 2

    def test_max_results_caps_the_list(self):
        search, _ = make_search()
        assert len(search.search("x", max_results = 1)) == 1

    def test_a_challenge_page_is_an_error_not_an_empty_search(self):
        search, _ = make_search(DUCKDUCKGO_CHALLENGE_PAGE)
        with pytest.raises(WebAccessError, match = "rate limited"):
            search.search("x")

    def test_a_page_without_results_is_an_empty_list(self):
        search, _ = make_search("<html><body><div class='no-results'>No results.</div></body></html>")
        assert search.search("zxqv") == []
