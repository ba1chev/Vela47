from typing import Optional

from app.intelligence.loaders import LoaderBase
from app.intelligence.loaders import LoaderType
from app.intelligence.loaders import LoaderDocument


class LoaderText(LoaderBase):
    """Reads a file that already is text — plain text, Markdown, CSV, JSON, a log. The only
    work is decoding: the declared charset when there is one, UTF-8 otherwise, and a
    lossless single-byte fallback for the legacy files that are neither, so an odd byte
    costs one replaced character instead of the whole upload."""

    @property
    def loader_type(self) -> LoaderType:
        return LoaderType.TEXT

    def load(self, data: bytes, encoding: Optional[str] = None) -> LoaderDocument:
        return LoaderDocument(
            text = self._tidy(self._decode(data, encoding)),
            loader_type = self.loader_type
        )
