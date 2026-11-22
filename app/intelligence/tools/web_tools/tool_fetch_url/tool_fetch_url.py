import re
from typing import Optional
from urllib.parse import urldefrag

from app.intelligence.tools import ToolBase
from app.intelligence.web import WebFetcher
from app.intelligence.loaders import LoaderType
from app.intelligence.messages import MessageTool
from app.intelligence.messages import MessageBase
from app.intelligence.messages import MessageHuman
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

    It opens only an address the conversation has already shown, exactly as shown: one
    in the task or in a result of a tool named in link_sources, web_search by default.
    Links inside fetched pages never count, so text injected into a page cannot make the
    agent send what it read from the user's documents to an address of its own. A page
    is fetched once per tool, which is once per task, and kept while the agent pages
    through it; one with no text is reported as such with a pointer to another source."""

    URL_PATTERN = re.compile(r"https?://[^\s<>\"'`]+")
    TRAILING_CHARS = ".,;:!?)]}*_"

    def __init__(self, web_fetcher: WebFetcher,
        loaders_factory: Optional[LoadersFactoryBase] = None,
        link_sources: tuple[str, ...] = ("web_search",)) -> None:
        super().__init__()
        self._web_fetcher: WebFetcher = web_fetcher
        self._loaders_factory: LoadersFactoryBase = (
            loaders_factory if loaders_factory is not None else LoadersFactory()
        )
        self._link_sources: tuple[str, ...] = link_sources
        self._shown: set[str] = set()
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

    def _normalize(self, url: str) -> str:
        return urldefrag(url.strip().rstrip(self.TRAILING_CHARS))[0].rstrip("/")

    def observe(self, message: MessageBase) -> None:
        shows_links = isinstance(message, MessageHuman) or (
            isinstance(message, MessageTool) and message.name in self._link_sources
        )
        if not shows_links:
            return
        text = message.content if isinstance(message.content, str) else str(message.content)
        self._shown.update(self._normalize(current_url) for current_url in self.URL_PATTERN.findall(text))

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
        if self._normalize(input.url) not in self._shown:
            raise ValueError(
                f"{input.url.strip()} was not in your task or in a web_search result, and "
                f"fetch_url opens only those addresses, exactly as they were given. Search "
                f"for the page with web_search first, then open a result."
            )
        final_url, document, truncated = self._load(urldefrag(input.url.strip())[0])
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
