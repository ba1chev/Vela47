from app.intelligence.tools import ToolWebSearch
from app.intelligence.web import WebSearchResult
from app.intelligence.tools import ToolWebSearchInput
from tests.fixtures.web.fake_web_search import FakeWebSearch

RESULTS = [
    WebSearchResult(title = "pytest docs", url = "https://docs.pytest.org/", snippet = "Full of fixtures."),
    WebSearchResult(title = "A blog", url = "https://blog.example.org/post", snippet = "x" * 1000)
]


class TestToolWebSearch:
    def test_name_is_stable(self):
        assert ToolWebSearch(FakeWebSearch()).name == "web_search"

    def test_results_list_title_url_and_snippet(self):
        output = ToolWebSearch(FakeWebSearch(RESULTS)).execute(ToolWebSearchInput(query = "pytest"))
        assert output.startswith("2 result(s) for 'pytest':")
        assert "[1] pytest docs\nhttps://docs.pytest.org/\nFull of fixtures." in output

    def test_the_result_reminds_that_snippets_are_not_sources(self):
        output = ToolWebSearch(FakeWebSearch(RESULTS)).execute(ToolWebSearchInput(query = "pytest"))
        assert output.endswith("fetch a page to read what it says.")

    def test_snippets_are_capped(self):
        output = ToolWebSearch(FakeWebSearch(RESULTS)).execute(ToolWebSearchInput(query = "pytest"))
        assert "x" * ToolWebSearch.MAX_SNIPPET_CHARS in output and "x" * (ToolWebSearch.MAX_SNIPPET_CHARS + 1) not in output

    def test_max_results_reaches_the_backend(self):
        backend = FakeWebSearch(RESULTS)
        ToolWebSearch(backend).execute(ToolWebSearchInput(query = "pytest", max_results = 1))
        assert backend.queries == [("pytest", 1)]

    def test_no_results_suggests_other_keywords(self):
        assert "found nothing" in ToolWebSearch(FakeWebSearch()).execute(ToolWebSearchInput(query = "zxqv"))
