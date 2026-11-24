import re
from typing import Optional

from app.intelligence.agents import RagMetadataType
from app.intelligence.agents import RagMetadataDocument
from app.intelligence.memory import VectorDbMemorySource
from app.intelligence.memory import VectorDbMemoryMetadata
from app.intelligence.agents import RagMetadataExtractorBase


class RagMetadataExtractorSection(RagMetadataExtractorBase):
    """Names the section a chunk sits in by its Markdown headings: the deepest section
    that holds all of the chunk's text, 'Operations Runbook › Error codes'. That is the
    part the heading paths where its text begins and where it ends have in common —
    compared heading by heading, not by title — so a chunk spanning two subsections is
    named by their parent, and headings at either edge of a chunk are not its text.
    Markdown is what every loader produces (HTML and Word headings become '#' lines),
    and lines inside fenced code are skipped, so a '# comment' is never a heading.

    A chunk whose text begins before the first heading, or that has no place in the
    document, gets no section."""

    HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*$")
    FENCE = re.compile(r"^[ \t]*(```|~~~)")
    SEPARATOR = " › "

    @property
    def metadata_type(self) -> RagMetadataType:
        return RagMetadataType.SECTION

    def _headings(self, text: str) -> list[tuple[int, int, str]]:
        headings: list[tuple[int, int, str]] = []
        offset, fenced = 0, False
        for current_line in text.splitlines(keepends = True):
            match = self.HEADING.match(current_line.rstrip("\r\n"))
            if self.FENCE.match(current_line):
                fenced = not fenced
            elif match is not None and not fenced:
                headings.append((offset, len(match.group(1)), match.group(2).strip()))
            offset += len(current_line)
        return headings

    def _text_edges(self, document: RagMetadataDocument, source: VectorDbMemorySource) -> Optional[tuple[int, int]]:
        if source.start is None or source.end is None:
            return None

        lines: list[int] = []
        offset = source.start
        for current_line in document.text[source.start:source.end].splitlines(keepends = True):
            if current_line.strip() and self.HEADING.match(current_line.rstrip("\r\n")) is None:
                lines.append(offset)
            offset += len(current_line)
        last = max(source.start, source.end - 1)
        return (lines[0], lines[-1]) if lines else (last, last)

    def _path_at(self, headings: list[tuple[int, int, str]], position: int) -> list[tuple[int, int, str]]:
        path: list[tuple[int, int, str]] = []
        for current_heading in headings:
            if current_heading[0] > position:
                break
            path = [current for current in path if current[1] < current_heading[1]] + [current_heading]
        return path

    def _section(self, headings: list[tuple[int, int, str]], edges: Optional[tuple[int, int]]) -> Optional[str]:
        if edges is None:
            return None

        common: list[tuple[int, int, str]] = []
        for current_first, current_last in zip(self._path_at(headings, edges[0]), self._path_at(headings, edges[1])):
            if current_first != current_last:
                break
            common.append(current_first)
        return self.SEPARATOR.join(title for _, _, title in common) or None

    def apply(self, document: RagMetadataDocument,
        metadata: list[VectorDbMemoryMetadata]) -> list[VectorDbMemoryMetadata]:
        headings = self._headings(document.text)
        return [
            current.model_copy(update = {
                "section": self._section(headings, self._text_edges(document, current.source))
            })
            for current in metadata
        ]
