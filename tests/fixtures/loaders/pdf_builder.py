class PdfBuilder:
    """Writes a small but valid PDF — catalog, page tree, one Helvetica font, a content
    stream per page and a correct cross-reference table — that pypdf reads like any real
    one. Each page is a string whose lines are drawn one below the other; an empty
    string makes a page with no text, which is what a scanned page looks like to a text
    extractor. Exists because no PDF writer is a dependency, and a binary fixture file
    would hide what a test is reading."""

    def _escape(self, text):
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def _stream(self, text):
        drawn = " 0 -16 Td ".join(f"({self._escape(current_line)}) Tj" for current_line in text.split("\n")) if text else ""
        return f"BT /F1 12 Tf 72 720 Td {drawn} ET".encode("latin-1")

    def build(self, pages, title = None):
        bodies = {
            1: b"<< /Type /Catalog /Pages 2 0 R >>",
            2: (
                "<< /Type /Pages /Kids [" + " ".join(f"{4 + 2 * index} 0 R" for index in range(len(pages)))
                + f"] /Count {len(pages)} >>"
            ).encode("latin-1"),
            3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
        }
        for index, current_page in enumerate(pages):
            page_id = 4 + 2 * index
            stream = self._stream(current_page)
            bodies[page_id] = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {page_id + 1} 0 R >>"
            ).encode("latin-1")
            bodies[page_id + 1] = f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream"

        info_id = 4 + 2 * len(pages)
        if title is not None:
            bodies[info_id] = f"<< /Title ({self._escape(title)}) >>".encode("latin-1")

        output = bytearray(b"%PDF-1.4\n")
        offsets = {}
        for object_id in sorted(bodies):
            offsets[object_id] = len(output)
            output += f"{object_id} 0 obj\n".encode("latin-1") + bodies[object_id] + b"\nendobj\n"

        xref_offset = len(output)
        size = max(bodies) + 1
        output += f"xref\n0 {size}\n0000000000 65535 f \n".encode("latin-1")
        for object_id in range(1, size):
            output += f"{offsets[object_id]:010d} 00000 n \n".encode("latin-1")

        info = f" /Info {info_id} 0 R" if title is not None else ""
        output += f"trailer\n<< /Size {size} /Root 1 0 R{info} >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin-1")
        return bytes(output)
