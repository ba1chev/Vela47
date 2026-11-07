from app.intelligence.agents import RagChunkerBase
from app.intelligence.agents import RagChunkerType


class RagChunkerRecursive(RagChunkerBase):
    """Cuts text along its own structure. The text is split on the coarsest separator
    first — blank lines, so paragraphs stay whole — and only a piece still longer than a
    chunk is split again on the next one: line breaks, then sentence ends, then spaces,
    and as a last resort at a fixed width. The pieces are then packed back together,
    greedily, into chunks as long as allowed.

    Each chunk after the first starts with the tail of the previous one, as many whole
    pieces as fit in the overlap, so the overlap never cuts a sentence in half. Separators
    stay attached to the text they ended, which keeps every chunk a verbatim slice of the
    document — the passage the agent cites is exactly what the document says."""

    SEPARATORS = ("\n\n", "\n", ". ", " ")

    @property
    def chunker_type(self) -> RagChunkerType:
        return RagChunkerType.RECURSIVE

    def _split(self, text: str, separators: tuple[str, ...]) -> list[str]:
        if len(text) <= self._chunk_chars:
            return [text]
        if not separators:
            return [text[start:start + self._chunk_chars] for start in range(0, len(text), self._chunk_chars)]

        separator, remaining = separators[0], separators[1:]
        if separator not in text:
            return self._split(text, remaining)

        parts = text.split(separator)
        parts = [current_part + separator for current_part in parts[:-1]] + [parts[-1]]

        pieces: list[str] = []
        for current_part in parts:
            if current_part:
                pieces.extend(self._split(current_part, remaining))
        return pieces

    def chunk(self, text: str) -> list[str]:
        chunks: list[str] = []
        current: list[str] = []

        for current_piece in self._split(text.strip(), self.SEPARATORS):
            if current and sum(map(len, current)) + len(current_piece) > self._chunk_chars:
                chunks.append("".join(current).strip())
                while current and sum(map(len, current)) > self._overlap_chars:
                    current.pop(0)
            current.append(current_piece)

        if current:
            chunks.append("".join(current).strip())
        return [current_chunk for current_chunk in chunks if current_chunk]
