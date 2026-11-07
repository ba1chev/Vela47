import re
from typing import Optional

from app.intelligence.loaders import LoaderBase
from app.intelligence.loaders import LoaderType
from app.intelligence.loaders import LoaderDocument
from app.intelligence.loaders import LoaderHtmlParser


class LoaderHtml(LoaderBase):
    """Reads a web page, or an uploaded .html file, down to its readable content and its
    <title>. The parsing is LoaderHtmlParser's; what this adds is finding the charset,
    which a page may declare in a header the caller passes as encoding or only in a
    <meta> tag near the top of the markup — so the first few kilobytes are searched for
    it before falling back to UTF-8.

    Built on the standard library's HTMLParser rather than a dependency: it is lenient
    with the broken markup real sites serve, and extracting text needs no DOM."""

    CHARSET_SCAN_BYTES = 4096
    CHARSET_PATTERN = re.compile(rb"""<meta[^>]+charset\s*=\s*["']?([A-Za-z0-9_\-]+)""", re.IGNORECASE)

    @property
    def loader_type(self) -> LoaderType:
        return LoaderType.HTML

    def _declared_charset(self, data: bytes) -> Optional[str]:
        match = self.CHARSET_PATTERN.search(data[:self.CHARSET_SCAN_BYTES])
        return match.group(1).decode("ascii") if match else None

    def load(self, data: bytes, encoding: Optional[str] = None) -> LoaderDocument:
        parser = LoaderHtmlParser()
        parser.feed(self._decode(data, encoding or self._declared_charset(data)))
        parser.close()

        return LoaderDocument(
            text = self._tidy(parser.text),
            title = parser.title,
            loader_type = self.loader_type
        )
