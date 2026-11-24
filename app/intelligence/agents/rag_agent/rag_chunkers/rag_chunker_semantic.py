import re
import math
from operator import mul

from app.intelligence.model import ModelEmbeddings
from app.intelligence.agents import RagChunkerBase
from app.intelligence.agents import RagChunkerType
from app.intelligence.agents import RagChunkSearchBase
from app.intelligence.agents import RagChunkSearchType
from app.intelligence.agents import RagChunkSearchFactory


class RagChunkerSemantic(RagChunkerBase):
    """Cuts text between sentences so that each chunk keeps to one topic. Adding a
    sentence costs more the less it adds to the summed embedding of its chunk; cutting
    costs a fixed fee, less where the similarity of the K sentences on either side dips
    (the TextTiling depth) and less again at a paragraph break. All the cuts of a
    document are then chosen together by the search SEARCH_TYPE names, which keeps every
    chunk within chunk_chars and above min_chars (see RagChunkSearchBase).

    Every chunk is a verbatim slice of the document. Chunks do not overlap, since a cut
    never falls inside a sentence. The sentences are embedded once per document, on top
    of the chunks the indexer embeds afterwards."""

    UNIT_END = re.compile(r"(?<=[.!?…])\s+|\n\s*")
    SEARCH_TYPE = RagChunkSearchType.A_STAR

    def __init__(self, embeddings: ModelEmbeddings, chunk_chars: int = 800, min_chars: int = 200,
        window_sentences: int = 3, extend_weight: float = 1.0, cut_weight: float = 1.0,
        cut_fee: float = 1.2, paragraph_discount: float = 0.8) -> None:
        super().__init__(chunk_chars, 0)
        if window_sentences < 1:
            raise ValueError("The window must hold at least one sentence.")
        if min(extend_weight, cut_weight, cut_fee, paragraph_discount) < 0:
            raise ValueError("Weights, the cut fee and the paragraph discount cannot be negative.")

        self._embeddings: ModelEmbeddings = embeddings
        self._chunk_search: RagChunkSearchBase = RagChunkSearchFactory().create(
            self.SEARCH_TYPE, chunk_chars = chunk_chars, min_chars = min_chars
        )
        self._window_sentences: int = window_sentences
        self._extend_weight: float = extend_weight
        self._cut_weight: float = cut_weight
        self._cut_fee: float = cut_fee
        self._paragraph_discount: float = paragraph_discount

    @property
    def chunker_type(self) -> RagChunkerType:
        return RagChunkerType.SEMANTIC

    def _units(self, text: str) -> list[str]:
        units: list[str] = []
        previous = 0
        for match in [*self.UNIT_END.finditer(text), None]:
            end = match.end() if match is not None else len(text)
            current_unit = text[previous:end]
            previous = end
            while len(current_unit) > self._chunk_chars:
                cut = current_unit.rfind(" ", 0, self._chunk_chars) + 1 or self._chunk_chars
                units.append(current_unit[:cut])
                current_unit = current_unit[cut:]
            if current_unit.strip():
                units.append(current_unit)

        return units

    def _vectors(self, units: list[str]) -> list[list[float]]:
        vectors = self._embeddings.embed_many([current_unit.strip() for current_unit in units])
        result: list[list[float]] = []
        for current_vector in vectors:
            norm = math.sqrt(sum(map(mul, current_vector, current_vector))) or 1.0
            result.append([value / norm for value in current_vector])
        return result

    def _cut_costs(self, units: list[str], vectors: list[list[float]]) -> list[float]:
        count, window = len(units), self._window_sentences
        similarities = [0.0] * count
        for gap in range(1, count):
            left = [sum(values) for values in zip(*vectors[max(0, gap - window):gap])]
            right = [sum(values) for values in zip(*vectors[gap:gap + window])]
            norms = math.sqrt(sum(map(mul, left, left))) * math.sqrt(sum(map(mul, right, right)))
            similarities[gap] = sum(map(mul, left, right)) / norms if norms else 0.0

        costs = [0.0] * count
        for gap in range(1, count):
            left_peak = right_peak = gap
            while left_peak > 1 and similarities[left_peak - 1] >= similarities[left_peak]:
                left_peak -= 1
            while right_peak < count - 1 and similarities[right_peak + 1] >= similarities[right_peak]:
                right_peak += 1
            depth = min(1.0, similarities[left_peak] + similarities[right_peak] - 2 * similarities[gap])
            paragraph = "\n\n" in units[gap - 1][len(units[gap - 1].rstrip()):]
            costs[gap] = max(0.0, self._cut_weight * (1 - depth) + self._cut_fee
                - (self._paragraph_discount if paragraph else 0.0))
        return costs

    def _extend_costs(self, lengths: list[int], vectors: list[list[float]]) -> dict[tuple[int, int], float]:
        overlaps: dict[tuple[int, int], float] = {}
        for index in range(1, len(vectors)):
            overlap, chars = 0.0, lengths[index]
            for start in range(index - 1, -1, -1):
                chars += lengths[start]
                if chars > self._chunk_chars:
                    break
                overlap += sum(map(mul, vectors[index], vectors[start]))
                overlaps[(start, index)] = overlap

        costs: dict[tuple[int, int], float] = {}
        for start in range(len(vectors)):
            norm_squared, index = 1.0, start + 1
            while (start, index) in overlaps:
                grown = max(0.0, norm_squared + 2 * overlaps[(start, index)] + 1.0)
                gain = math.sqrt(grown) - math.sqrt(norm_squared)
                costs[(start, index)] = max(0.0, self._extend_weight * (1 - gain))
                norm_squared, index = grown, index + 1
        return costs

    def chunk(self, text: str) -> list[str]:
        units = self._units(text.strip())
        if len(units) <= 1:
            return [current_unit.strip() for current_unit in units]

        lengths = [len(current_unit) for current_unit in units]
        vectors = self._vectors(units)
        starts = self._chunk_search.search(lengths, self._cut_costs(units, vectors), self._extend_costs(lengths, vectors))

        return [
            "".join(units[start:end]).strip()
            for start, end in zip(starts, starts[1:] + [len(units)])
        ]
