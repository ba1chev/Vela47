import re
from typing import Optional
from abc import ABC, abstractmethod

from app.intelligence.loaders import LoaderType
from app.intelligence.loaders import LoaderDocument


class LoaderBase(ABC):
    """Abstract base for turning a file's bytes into the text an agent can read and the
    RAG agent can index. Loaders take bytes rather than paths because nothing they read
    is on disk: an upload arrives in a request body and a page arrives from the network.

    Every loader treats its input as hostile. The bytes come from a user or from an
    arbitrary website, so a file that cannot be read raises ValueError with a sentence
    that says why — the caller shows that sentence to a person or a model — rather than
    letting a parser's internal exception escape.

    The two helpers here are what the text-based loaders share: decoding that survives a
    wrong or missing charset, and tidying that leaves paragraphs separated by exactly one
    blank line, which is what the recursive chunker splits on first."""

    @property
    @abstractmethod
    def loader_type(self) -> LoaderType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def load(self, data: bytes, encoding: Optional[str] = None) -> LoaderDocument:
        raise NotImplementedError("Must be implemented")

    def _decode(self, data: bytes, encoding: Optional[str] = None) -> str:
        if encoding:
            try:
                return data.decode(encoding)
            except (LookupError, UnicodeDecodeError):
                pass
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError:
            return data.decode("cp1252", errors = "replace")

    def _tidy(self, text: str) -> str:
        lines = [current_line.rstrip() for current_line in text.replace("\r\n", "\n").split("\n")]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
