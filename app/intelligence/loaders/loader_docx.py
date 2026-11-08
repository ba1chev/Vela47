import io
import zipfile
from docx import Document
from typing import Optional
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.intelligence.loaders import LoaderBase
from app.intelligence.loaders import LoaderType
from app.intelligence.loaders import LoaderDocument


class LoaderDocx(LoaderBase):
    """Reads a Word document with python-docx, keeping body paragraphs and tables in the
    order they appear — a table in the middle of a section belongs to that section, and
    reading all paragraphs first would move it. Heading styles become Markdown headings
    and list styles become list items, so the structure survives as text.

    A .docx is a zip archive, and a small archive can inflate to gigabytes of XML. The
    declared sizes of its entries are checked before anything is parsed, so a hostile
    upload is refused instead of exhausting the server's memory."""

    MAX_UNCOMPRESSED_BYTES = 64 * 1024 * 1024

    @property
    def loader_type(self) -> LoaderType:
        return LoaderType.DOCX

    def _check_archive(self, data: bytes) -> None:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                inflated = sum(current_entry.file_size for current_entry in archive.infolist())
        except zipfile.BadZipFile:
            raise ValueError("The file is not a Word document (.docx).") from None
        if inflated > self.MAX_UNCOMPRESSED_BYTES:
            raise ValueError("The Word document expands to more than its size allows and was refused.")

    def _paragraph(self, paragraph: Paragraph) -> str:
        text = paragraph.text.strip()
        style = (paragraph.style.name if paragraph.style is not None else "") or ""

        if not text:
            return ""
        if style == "Title":
            return f"# {text}"
        if style.startswith("Heading"):
            level = style.removeprefix("Heading").strip()
            return "#" * min(int(level) if level.isdigit() else 1, 6) + f" {text}"
        if "List" in style:
            return f"- {text}"
        return text

    def _table(self, table: Table) -> str:
        rows = []
        for current_row in table.rows:
            cells: list[str] = []
            for current_cell in current_row.cells:
                text = " ".join(current_cell.text.split())
                if not cells or cells[-1] != text:
                    cells.append(text)
            if any(cells):
                rows.append(" | ".join(cells))
        return "\n".join(rows)

    def load(self, data: bytes, encoding: Optional[str] = None) -> LoaderDocument:
        self._check_archive(data)
        try:
            document = Document(io.BytesIO(data))
        except Exception as error:
            raise ValueError(f"The Word document could not be opened: {error}") from None

        blocks = [
            self._paragraph(current_block)
            if isinstance(current_block, Paragraph)
            else self._table(current_block)
            for current_block in document.iter_inner_content()
        ]
        title = (document.core_properties.title or "").strip()

        return LoaderDocument(
            text = self._tidy("\n\n".join(current_block for current_block in blocks if current_block)),
            title = title or None,
            loader_type = self.loader_type
        )
