import re
import math
from operator import mul
from collections import Counter

from app.intelligence.model import ModelEmbeddings
from app.intelligence.agents import RagMetadataType
from app.intelligence.agents import RagMetadataDocument
from app.intelligence.memory import VectorDbMemoryMetadata
from app.intelligence.agents import RagMetadataExtractorBase


class RagMetadataExtractorKeywords(RagMetadataExtractorBase):
    """Picks the words of a chunk that best say what it is about, in two passes. BM25
    first proposes `candidates` words that are frequent in the chunk and rare among the
    document's sentences — no stop word list, in any language. A one-chunk document
    gives those statistics nothing to compare, so the candidates are then embedded,
    once per document in one batch, and the max_keywords closest to the chunk's own
    vector are kept.

    Words shorter than three characters and bare numbers are left out, while words with
    digits in them — an error code, a version — are kept. Each keyword is written as
    the document first writes it."""

    SENTENCE_END = re.compile(r"(?<=[.!?…])\s+|\n\s*")
    WORD = re.compile(r"\w+")
    MIN_CHARS = 3
    K1 = 1.5

    def __init__(self, embeddings: ModelEmbeddings, max_keywords: int = 5, candidates: int = 15) -> None:
        if not 1 <= max_keywords <= candidates:
            raise ValueError("At least one keyword must be kept, and no more than there are candidates.")

        self._embeddings: ModelEmbeddings = embeddings
        self._max_keywords: int = max_keywords
        self._candidates: int = candidates

    @property
    def metadata_type(self) -> RagMetadataType:
        return RagMetadataType.KEYWORDS

    def _words(self, text: str) -> list[str]:
        return [
            current_word
            for current_word in self.WORD.findall(text)
            if len(current_word) >= self.MIN_CHARS and not current_word.isdigit()
        ]

    def _unit(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(map(mul, vector, vector))) or 1.0
        return [value / norm for value in vector]

    def _candidates_of(self, chunk: str, sentence_frequencies: Counter, sentence_count: int) -> list[str]:
        frequencies = Counter(current_word.lower() for current_word in self._words(chunk))
        scores = {
            current_term: current_frequency * (self.K1 + 1.0) / (current_frequency + self.K1) * math.log(
                1.0 + (sentence_count - sentence_frequencies[current_term] + 0.5)
                / (sentence_frequencies[current_term] + 0.5)
            )
            for current_term, current_frequency in frequencies.items()
        }
        return sorted(scores, key = lambda current_term: scores[current_term], reverse = True)[:self._candidates]

    def apply(self, document: RagMetadataDocument,
        metadata: list[VectorDbMemoryMetadata]) -> list[VectorDbMemoryMetadata]:
        spellings: dict[str, str] = {}
        for current_word in self._words(document.text):
            spellings.setdefault(current_word.lower(), current_word)

        sentences = [current for current in self.SENTENCE_END.split(document.text) if current.strip()]
        sentence_frequencies: Counter = Counter()
        for current_sentence in sentences:
            sentence_frequencies.update({current_word.lower() for current_word in self._words(current_sentence)})

        candidates = [
            self._candidates_of(current_chunk, sentence_frequencies, len(sentences))
            for current_chunk in document.chunks
        ]
        terms = list(dict.fromkeys(current_term for current in candidates for current_term in current))
        vectors = self._embeddings.embed_many([spellings.get(current, current) for current in terms]) if terms else []
        term_vectors = {current_term: self._unit(current_vector) for current_term, current_vector in zip(terms, vectors)}

        result: list[VectorDbMemoryMetadata] = []
        for current_terms, current_vector, current_metadata in zip(candidates, document.vectors, metadata):
            unit = self._unit(current_vector)
            ranked = sorted(
                current_terms,
                key = lambda current_term: sum(map(mul, unit, term_vectors[current_term])),
                reverse = True
            )
            result.append(current_metadata.model_copy(update = {
                "keywords": [spellings.get(current_term, current_term) for current_term in ranked[:self._max_keywords]]
            }))
        return result
