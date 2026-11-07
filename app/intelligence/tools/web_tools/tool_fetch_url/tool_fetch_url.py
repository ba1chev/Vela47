from typing import Optional

from app.intelligence.tools import ToolBase
from app.intelligence.web import WebFetcher
from app.intelligence.loaders import LoadersFactory
from app.intelligence.loaders import LoaderDocument
from app.intelligence.tools import ToolFetchUrlInput
from app.intelligence.loaders import LoadersFactoryBase
from app.intelligence.loaders import resolve_loader_type


class ToolFetchUrl(ToolBase[ToolFetchUrlInput, str]):
    """Reads a web page — or a PDF or Word document online — as plain text, a window of
    characters at a time, the way MCP's fetch server does with start_index and
    max_length.

    The page is fetched through the WebFetcher, so only public addresses are reachable,
    and read by the loader its content type calls for: an HTML page loses its navigation
    and scripts, a PDF is read for its text layer. What comes back starts with the
    page's title and its final URL — the one to cite after redirects.

    A page is fetched once per tool, which is once per subagent task, and kept in
    memory while the agent pages through it: asking for characters 4000 to 8000 should
    not download the page again, and should not risk the second download differing from
    the first."""

    def __init__(self, web_fetcher: WebFetcher,
        loaders_factory: Optional[LoadersFactoryBase] = None) -> None:
        super().__init__()
        self._web_fetcher: WebFetcher = web_fetcher
        self._loaders_factory: LoadersFactoryBase = (
            loaders_factory if loaders_factory is not None else LoadersFactory()
        )
        self._pages: dict[str, tuple[str, LoaderDocument, bool]] = {}

    @property
    def name(self) -> str:
        return "fetch_url"

    @property
    def description(self) -> str:
        return (
            "Read a web page, or a PDF or Word document online, as plain text. Long pages "
            "come back in parts; the result says which start_index continues it. Use it to "
            "read a source before you rely on it, and cite its URL."
        )

    @property
    def input_schema(self) -> type[ToolFetchUrlInput]:
        return ToolFetchUrlInput

    def _load(self, url: str) -> tuple[str, LoaderDocument, bool]:
        if url in self._pages:
            return self._pages[url]

        page = self._web_fetcher.fetch(url)
        loader_type = resolve_loader_type(page.url, page.content_type)
        if loader_type is None:
            raise ValueError(
                f"{page.url} is {page.content_type or 'of an unknown type'}, which cannot be "
                f"read as text."
            )

        document = self._loaders_factory.create(loader_type).load(page.content, page.encoding)
        self._pages[url] = (page.url, document, page.truncated)
        return self._pages[url]

    def execute(self, input: ToolFetchUrlInput) -> str:
        final_url, document, truncated = self._load(input.url.strip())
        text = document.text
        if not text:
            return f"{final_url} was fetched but holds no readable text."
        if input.start_index >= len(text):
            return (
                f"{final_url} has {len(text)} characters of text, so there is nothing from "
                f"start_index {input.start_index} on."
            )

        end = min(len(text), input.start_index + input.max_length)
        header = f"{document.title or 'Untitled'} — {final_url}\n(characters {input.start_index}-{end} of {len(text)}"
        header += ", the page itself was cut short at the size limit)" if truncated else ")"

        footer = ""
        if end < len(text):
            footer = (
                f"\n\n… {len(text) - end} more characters. Call fetch_url with "
                f"start_index={end} to continue."
            )
        return f"{header}\n\n{text[input.start_index:end]}{footer}"
