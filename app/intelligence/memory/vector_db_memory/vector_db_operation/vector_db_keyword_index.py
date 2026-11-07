import math
from collections import Counter

from app.intelligence.memory import tokenize
from app.intelligence.memory import VectorDbMemoryEntry


class VectorDbKeywordIndex:
    """BM25 over the text of a fixed list of entries — the lexical half of hybrid
    search. Dense vectors match meaning but blur exact tokens: a function name, an error
    code, a version number come out close to anything that merely sounds related. BM25
    rewards exactly those tokens, weights rare terms above common ones, and discounts
    long passages so that length alone never wins.

    Built for one list of entries and thrown away with it. Entries are loaded per
    request, so an index kept between requests would only ever describe a list nobody is
    searching any more. Tokens are lower-cased Unicode words, which keeps Cyrillic and
    Latin text equally searchable."""

    K1 = 1.5
    B = 0.75

    def __init__(self, entries: list[VectorDbMemoryEntry]) -> None:
        documents = [tokenize(self._text_of(current_entry)) for current_entry in entries]
        self._frequencies: list[Counter] = [Counter(current_document) for current_document in documents]
        self._lengths: list[int] = [len(current_document) for current_document in documents]
        self._average_length: float = (sum(self._lengths) / len(self._lengths)) if self._lengths else 0.0

        containing: Counter = Counter()
        for current_document in documents:
            containing.update(set(current_document))
        count = len(documents)
        self._idf: dict[str, float] = {
            current_term: math.log(1.0 + (count - current_count + 0.5) / (current_count + 0.5))
            for current_term, current_count in containing.items()
        }

    def _text_of(self, entry: VectorDbMemoryEntry) -> str:
        content = entry.message.content
        return content if isinstance(content, str) else str(content)

    def scores(self, query: str) -> list[float]:
        terms = tokenize(query)
        result: list[float] = []

        for current_frequencies, current_length in zip(self._frequencies, self._lengths):
            score = 0.0
            for current_term in terms:
                frequency = current_frequencies.get(current_term, 0)
                if frequency == 0:
                    continue
                normalised = 1.0 - self.B + self.B * (current_length / self._average_length if self._average_length else 0.0)
                score += self._idf[current_term] * frequency * (self.K1 + 1.0) / (frequency + self.K1 * normalised)
            result.append(score)

        return result
