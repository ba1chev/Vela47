import io
import re
from typing import Optional
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from app.intelligence.loaders import LoaderBase
from app.intelligence.loaders import LoaderType
from app.intelligence.loaders import LoaderDocument


class LoaderPdf(LoaderBase):
    """Reads the text layer of a PDF, page by page, with pypdf.

    Pages are joined by a blank line so a chunker never glues the last sentence of one
    page to the first of the next. A word hyphenated across a line break is joined back,
    since 'retrie-\\nval' is two words to keyword search and to the embedding alike.

    A PDF without a text layer — a scan, a photographed page — has nothing to read
    without OCR, and is refused with that explanation rather than indexed as an empty
    document. An encrypted PDF is opened when it has no user password, which is how
    most 'protected' PDFs are distributed, and refused otherwise."""

    HYPHENATED_BREAK = re.compile(r"(\w)-\n(\w)")

    @property
    def loader_type(self) -> LoaderType:
        return LoaderType.PDF

    def load(self, data: bytes, encoding: Optional[str] = None) -> LoaderDocument:
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted and not reader.decrypt(""):
                raise ValueError("The PDF is password protected and cannot be read.")
            pages = [current_page.extract_text() or "" for current_page in reader.pages]
            metadata = reader.metadata
        except PyPdfError as error:
            raise ValueError(f"The file is not a readable PDF: {error}") from None

        text = self._tidy(self.HYPHENATED_BREAK.sub(r"\1\2", "\n\n".join(pages)))
        if not text:
            raise ValueError(
                "The PDF has no text layer — it is probably scanned images, which cannot be "
                "read without OCR."
            )

        title = (metadata.title or "").strip() if metadata is not None else ""
        return LoaderDocument(text = text, title = title or None, loader_type = self.loader_type)
