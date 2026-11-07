from app.intelligence.tools import ToolBase
from app.intelligence.web import WebSearchBase
from app.intelligence.tools import ToolWebSearchInput


class ToolWebSearch(ToolBase[ToolWebSearchInput, str]):
    """Searches the web and lists each result's title, URL and snippet.

    A snippet is the search engine's excerpt, not the page, and small models readily
    quote it as if it were a source. The result therefore ends by saying so: the
    snippets are for choosing which page to open with fetch_url, and a fact is only
    established once it has been read there.

    Whichever backend is injected does the searching — DuckDuckGo by default — so
    changing engines changes nothing here."""

    MAX_SNIPPET_CHARS = 300

    def __init__(self, web_search: WebSearchBase) -> None:
        super().__init__()
        self._web_search: WebSearchBase = web_search

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search the web and get back a list of pages, each with its title, URL and a "
            "short snippet. Use it to find sources; then read the most promising pages "
            "with fetch_url before relying on what they say."
        )

    @property
    def input_schema(self) -> type[ToolWebSearchInput]:
        return ToolWebSearchInput

    def execute(self, input: ToolWebSearchInput) -> str:
        results = self._web_search.search(input.query, input.max_results)
        if not results:
            return f"The web search for '{input.query}' found nothing. Try fewer or different keywords."

        listed = "\n\n".join(
            f"[{index}] {current_result.title}\n{current_result.url}\n"
            f"{current_result.snippet[:self.MAX_SNIPPET_CHARS]}".rstrip()
            for index, current_result in enumerate(results, start = 1)
        )
        return (
            f"{len(results)} result(s) for '{input.query}':\n\n{listed}\n\n"
            f"Snippets are excerpts, not sources — fetch a page to read what it says."
        )
