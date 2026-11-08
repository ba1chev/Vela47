import httpx
import pytest

from app.intelligence.web import WebFetcher
from app.intelligence.web import WebAccessError
from app.intelligence.web import WebAddressGuard
from tests.fixtures.web.fake_resolver import FakeResolver
from tests.fixtures.web.fake_web_server import FakeWebServer


def make_fetcher(routes, table = None, **kwargs):
    server = FakeWebServer(routes)
    resolver = FakeResolver(table)
    return WebFetcher(WebAddressGuard(resolver), transport = server.transport, **kwargs), server, resolver


class TestWebFetcher:
    def test_a_page_comes_back_with_its_type_and_charset(self):
        fetcher, _, _ = make_fetcher({"https://example.org/a": FakeWebServer.page("<p>hi</p>")})
        page = fetcher.fetch("https://example.org/a")
        assert page.content == b"<p>hi</p>" and page.content_type == "text/html" and page.encoding == "utf-8"
        assert page.url == "https://example.org/a" and page.status_code == 200 and not page.truncated

    def test_the_request_goes_to_the_checked_address_under_the_original_name(self):
        fetcher, server, _ = make_fetcher(
            {"https://example.org/a": FakeWebServer.page("x")}, {"example.org": ["93.184.216.34"]}
        )
        fetcher.fetch("https://example.org/a")
        request = server.requests[0]
        assert request.url.host == "93.184.216.34" and request.headers["host"] == "example.org"
        assert request.extensions["sni_hostname"] == "example.org"

    def test_a_non_default_port_stays_in_the_host_header(self):
        fetcher, server, _ = make_fetcher({"http://example.org:8080/a": FakeWebServer.page("x")})
        fetcher.fetch("http://example.org:8080/a")
        assert server.requests[0].headers["host"] == "example.org:8080" and "sni_hostname" not in server.requests[0].extensions

    def test_a_redirect_is_followed_and_its_target_checked_again(self):
        fetcher, _, resolver = make_fetcher({
            "https://example.org/old": FakeWebServer.redirect("https://docs.example.org/new"),
            "https://docs.example.org/new": FakeWebServer.page("moved")
        })
        page = fetcher.fetch("https://example.org/old")
        assert page.content == b"moved" and page.url == "https://docs.example.org/new"
        assert resolver.lookups == ["example.org", "docs.example.org"]

    def test_a_relative_redirect_is_resolved_against_the_current_url(self):
        fetcher, _, _ = make_fetcher({
            "https://example.org/a/b": FakeWebServer.redirect("../c"),
            "https://example.org/c": FakeWebServer.page("here")
        })
        assert fetcher.fetch("https://example.org/a/b").content == b"here"

    def test_a_redirect_to_a_private_address_is_refused(self):
        fetcher, server, _ = make_fetcher({
            "https://example.org/x": FakeWebServer.redirect("http://169.254.169.254/latest/meta-data/")
        })
        with pytest.raises(WebAccessError, match = "not a public address"):
            fetcher.fetch("https://example.org/x")
        assert len(server.requests) == 1

    def test_a_post_redirected_with_303_becomes_a_get_without_its_form(self):
        fetcher, server, _ = make_fetcher({
            "https://example.org/search": FakeWebServer.redirect("https://example.org/results", status = 303),
            "https://example.org/results": FakeWebServer.page("results")
        })
        fetcher.fetch("https://example.org/search", form = {"q": "x"})
        assert [current.method for current in server.requests] == ["POST", "GET"]
        assert server.requests[0].content == b"q=x" and server.requests[1].content == b""

    def test_too_many_redirects_are_refused(self):
        fetcher, _, _ = make_fetcher(
            {"https://example.org/loop": FakeWebServer.redirect("https://example.org/loop")}, max_redirects = 2
        )
        with pytest.raises(WebAccessError, match = "redirected more than 2 times"):
            fetcher.fetch("https://example.org/loop")

    def test_an_error_status_is_raised(self):
        fetcher, _, _ = make_fetcher({})
        with pytest.raises(WebAccessError, match = "HTTP 404"):
            fetcher.fetch("https://example.org/missing")

    def test_a_body_over_the_limit_is_cut_and_flagged(self):
        fetcher, _, _ = make_fetcher({"https://example.org/big": FakeWebServer.page("x" * 5000)}, max_bytes = 1000)
        page = fetcher.fetch("https://example.org/big")
        assert len(page.content) == 1000 and page.truncated

    def test_the_limit_can_be_set_per_fetch(self):
        fetcher, _, _ = make_fetcher({"https://example.org/big": FakeWebServer.page("x" * 5000)})
        assert len(fetcher.fetch("https://example.org/big", max_bytes = 10).content) == 10

    def test_a_transport_failure_becomes_a_web_access_error(self):
        def refuse(request):
            raise httpx.ConnectError("connection refused", request = request)
        fetcher = WebFetcher(WebAddressGuard(FakeResolver()), transport = httpx.MockTransport(refuse))
        with pytest.raises(WebAccessError, match = "could not be fetched: ConnectError"):
            fetcher.fetch("https://example.org/")

    def test_something_that_is_not_a_full_url_is_refused(self):
        fetcher, _, _ = make_fetcher({})
        with pytest.raises(WebAccessError, match = "not a full URL"):
            fetcher.fetch("example.org/page")

    def test_a_private_target_is_refused_before_any_request(self):
        fetcher, server, _ = make_fetcher({}, {"localhost": ["127.0.0.1"]})
        with pytest.raises(WebAccessError):
            fetcher.fetch("http://localhost:8000/admin")
        assert server.requests == []
