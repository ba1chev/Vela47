from typing import Optional

from app.intelligence.tools import ToolBase
from app.intelligence.web import WebFetcher
from app.intelligence.loaders import LoaderType
from app.intelligence.loaders import LoadersFactory
from app.intelligence.loaders import LoaderDocument
from app.intelligence.tools import ToolFetchUrlInput
from app.intelligence.loaders import LoadersFactoryBase
from app.intelligence.loaders import resolve_loader_type


class ToolFetchUrl(ToolBase[ToolFetchUrlInput, str]):
    """Reads a web page, PDF or Word document as plain text, a window of characters at a
    time from start_index, like MCP's fetch server. The page goes through the
    WebFetcher, so only public addresses are reachable, and through the loader its
    content type calls for; the result starts with the title and the final URL to cite.

    A page is fetched once per tool, which is once per task, and kept while the agent
    pages through it. A page with no text, usually one drawn by JavaScript, is reported
    as such with a pointer to another source."""

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
            reason = (
                " It is probably built by JavaScript, which is not run here."
                if document.loader_type is LoaderType.HTML
                else ""
            )
            return f"{final_url} was fetched but holds no readable text.{reason} Try another source for the same information."
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
