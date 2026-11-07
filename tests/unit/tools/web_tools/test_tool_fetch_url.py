import pytest

from app.intelligence.web import WebFetcher
from app.intelligence.tools import ToolFetchUrl
from app.intelligence.web import WebAccessError
from app.intelligence.web import WebAddressGuard
from app.intelligence.tools import ToolFetchUrlInput
from tests.fixtures.web.fake_resolver import FakeResolver
from tests.fixtures.loaders.pdf_builder import PdfBuilder
from tests.fixtures.web.fake_web_server import FakeWebServer

ARTICLE = "<html><head><title>Release notes</title></head><body><nav>Menu</nav><p>" + "Version 2 adds hybrid search. " * 300 + "</p></body></html>"


def make_tool(routes):
    server = FakeWebServer(routes)
    return ToolFetchUrl(WebFetcher(WebAddressGuard(FakeResolver()), transport = server.transport)), server


class TestToolFetchUrl:
    def test_name_is_stable(self):
        assert make_tool({})[0].name == "fetch_url"

    def test_a_page_is_read_as_text_under_its_title_and_url(self):
        tool, _ = make_tool({"https://example.org/notes": FakeWebServer.page(ARTICLE)})
        output = tool.execute(ToolFetchUrlInput(url = "https://example.org/notes", max_length = 500))
        assert output.startswith("Release notes — https://example.org/notes\n(characters 0-500 of ")
        assert "Version 2 adds hybrid search." in output and "Menu" not in output

    def test_a_long_page_says_where_to_continue(self):
        tool, _ = make_tool({"https://example.org/notes": FakeWebServer.page(ARTICLE)})
        output = tool.execute(ToolFetchUrlInput(url = "https://example.org/notes", max_length = 500))
        assert "Call fetch_url with start_index=500 to continue." in output

    def test_paging_reuses_the_page_instead_of_fetching_it_again(self):
        tool, server = make_tool({"https://example.org/notes": FakeWebServer.page(ARTICLE)})
        tool.execute(ToolFetchUrlInput(url = "https://example.org/notes", max_length = 500))
        output = tool.execute(ToolFetchUrlInput(url = "https://example.org/notes", start_index = 500, max_length = 500))
        assert "(characters 500-1000 of " in output and len(server.requests) == 1

    def test_reading_past_the_end_is_explained(self):
        tool, _ = make_tool({"https://example.org/a": FakeWebServer.page("<p>short</p>")})
        assert "nothing from start_index 99" in tool.execute(ToolFetchUrlInput(url = "https://example.org/a", start_index = 99))

    def test_a_pdf_online_is_read_through_its_loader(self):
        pdf = PdfBuilder().build(["Quarterly report: revenue grew."], title = "Q3")
        tool, _ = make_tool({"https://example.org/q3.pdf": FakeWebServer.page(pdf, "application/pdf")})
        output = tool.execute(ToolFetchUrlInput(url = "https://example.org/q3.pdf"))
        assert output.startswith("Q3 — https://example.org/q3.pdf") and "revenue grew" in output

    def test_a_type_no_loader_reads_is_refused(self):
        tool, _ = make_tool({"https://example.org/logo": FakeWebServer.page(b"\x89PNG", "image/png")})
        with pytest.raises(ValueError, match = "image/png, which cannot be read as text"):
            tool.execute(ToolFetchUrlInput(url = "https://example.org/logo"))

    def test_a_private_address_is_refused(self):
        tool, server = make_tool({})
        with pytest.raises(WebAccessError):
            tool.execute(ToolFetchUrlInput(url = "http://169.254.169.254/latest/meta-data/"))
        assert server.requests == []
