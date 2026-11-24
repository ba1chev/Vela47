import re

from app.intelligence.model import ModelEmbeddings
from app.intelligence.agents import RagChunkerBase
from app.intelligence.agents import RagChunkerType
from app.intelligence.agents import RagChunkSearchBase
from app.intelligence.agents import RagChunkSearchType
from app.intelligence.agents import RagChunkSearchFactory
from app.intelligence.agents import RagSemanticScoringBase
from app.intelligence.agents import RagSemanticScoringType
from app.intelligence.agents import RagSemanticScoringFactory


class RagChunkerSemantic(RagChunkerBase):
    """Cuts text between sentences so that each chunk keeps to one topic. The chunker
    only splits the text into sentences; what each cut and each extension of a chunk
    costs comes from the scoring SCORING_TYPE names (see RagSemanticScoringTextTiling),
    and all the cuts of a document are then chosen together by the search SEARCH_TYPE
    names, which keeps every chunk within chunk_chars and above min_chars.

    Every chunk is a verbatim slice of the document. Chunks do not overlap, since a cut
    never falls inside a sentence. The sentences are embedded once per document, on top
    of the chunks the indexer embeds afterwards."""

    UNIT_END = re.compile(r"(?<=[.!?…])\s+|\n\s*")
    SCORING_TYPE = RagSemanticScoringType.TEXT_TILING
    SEARCH_TYPE = RagChunkSearchType.A_STAR

    def __init__(self, embeddings: ModelEmbeddings, chunk_chars: int = 800, min_chars: int = 200,
        window_sentences: int = 3, extend_weight: float = 1.0, cut_weight: float = 1.0,
        cut_fee: float = 1.2, paragraph_discount: float = 0.8) -> None:
        super().__init__(chunk_chars, 0)

        self._semantic_scoring: RagSemanticScoringBase = RagSemanticScoringFactory().create(
            self.SCORING_TYPE,
            embeddings = embeddings,
            chunk_chars = chunk_chars,
            window_sentences = window_sentences,
            extend_weight = extend_weight,
            cut_weight = cut_weight,
            cut_fee = cut_fee,
            paragraph_discount = paragraph_discount
        )
        self._chunk_search: RagChunkSearchBase = RagChunkSearchFactory().create(
            self.SEARCH_TYPE, chunk_chars = chunk_chars, min_chars = min_chars
        )

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

    def chunk(self, text: str) -> list[str]:
        units = self._units(text.strip())
        if len(units) <= 1:
            return [current_unit.strip() for current_unit in units]

        cut_costs, extend_costs = self._semantic_scoring.score(units)
        starts = self._chunk_search.search([len(current_unit) for current_unit in units], cut_costs, extend_costs)

        return [
            "".join(units[start:end]).strip()
            for start, end in zip(starts, starts[1:] + [len(units)])
        ]
