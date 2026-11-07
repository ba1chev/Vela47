from app.intelligence.agents import RagChunkerBase
from app.intelligence.agents import RagChunkerType


class RagChunkerFixed(RagChunkerBase):
    """Cuts text into windows of a constant width, each starting overlap_chars before
    the previous one ended. Blind to structure on purpose: for a log, a CSV or a single
    long line there are no paragraphs to follow, and a predictable width is worth more
    than a boundary that does not exist."""

    @property
    def chunker_type(self) -> RagChunkerType:
        return RagChunkerType.FIXED

    def chunk(self, text: str) -> list[str]:
        text = text.strip()
        step = self._chunk_chars - self._overlap_chars
        chunks: list[str] = []

        for start in range(0, len(text), step):
            chunks.append(text[start:start + self._chunk_chars].strip())
            if start + self._chunk_chars >= len(text):
                break

        return [current_chunk for current_chunk in chunks if current_chunk]
