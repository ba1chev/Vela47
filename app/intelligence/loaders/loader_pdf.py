import io
import re
from typing import Optional
from pypdf import PdfReader

from app.intelligence.loaders import LoaderBase
from app.intelligence.loaders import LoaderType
from app.intelligence.loaders import LoaderDocument


class LoaderPdf(LoaderBase):
    """Reads the text layer of a PDF page by page with pypdf. Pages are joined by a
    blank line, and a word hyphenated across a line break is joined back.

    A PDF with no text layer, such as a scan, is refused rather than indexed as empty.
    An encrypted PDF is opened when it has no user password and refused otherwise. Any
    failure inside pypdf, including the TypeError or KeyError it raises on damaged
    files, becomes the ValueError every loader raises, so an upload gets a sentence
    about the file instead of a server error."""

    HYPHENATED_BREAK = re.compile(r"(\w)-\n(\w)")

    @property
    def loader_type(self) -> LoaderType:
        return LoaderType.PDF

    def _open(self, data: bytes) -> PdfReader:
        try:
            reader = PdfReader(io.BytesIO(data))
            unlocked = not reader.is_encrypted or bool(reader.decrypt(""))
        except Exception as error:
            raise ValueError(f"The file is not a readable PDF: {error}") from None
        if not unlocked:
            raise ValueError("The PDF is password protected and cannot be read.")
        return reader

    def load(self, data: bytes, encoding: Optional[str] = None) -> LoaderDocument:
        reader = self._open(data)
        try:
            pages = [current_page.extract_text() or "" for current_page in reader.pages]
            metadata = reader.metadata
            title = (metadata.title or "").strip() if metadata is not None else ""
        except Exception as error:
            raise ValueError(f"The file is not a readable PDF: {error}") from None

        text = self._tidy(self.HYPHENATED_BREAK.sub(r"\1\2", "\n\n".join(pages)))
        if not text:
            raise ValueError(
                "The PDF has no text layer — it is probably scanned images, which cannot be "
                "read without OCR."
            )

        return LoaderDocument(text = text, title = title or None, loader_type = self.loader_type)
