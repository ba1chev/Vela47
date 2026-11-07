import zlib

from app.intelligence.memory import tokenize


class FakeEmbeddings:
    """Embeds text without Ollama: every word adds one to a fixed slot of a small
    vector, so texts sharing words point the same way and cosine similarity behaves
    sensibly. Slots come from crc32, not hash(), so a vector is the same on every run.
    Records every batch it was asked for, so a test can prove what was — and was not —
    embedded."""

    DIMENSIONS = 32

    def __init__(self) -> None:
        self.calls = []

    def _vector(self, text):
        vector = [0.0] * self.DIMENSIONS
        for word in tokenize(text):
            vector[zlib.crc32(word.encode("utf-8")) % self.DIMENSIONS] += 1.0
        return vector

    def embed_many(self, texts):
        self.calls.append(list(texts))
        return [self._vector(current_text) for current_text in texts]

    def embed(self, text):
        return self.embed_many([text])[0]
