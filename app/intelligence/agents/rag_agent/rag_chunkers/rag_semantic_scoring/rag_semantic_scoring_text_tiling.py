import math
from operator import mul

from app.intelligence.tracing import rounded
from app.intelligence.model import ModelEmbeddings
from app.intelligence.tracing import describe_numbers
from app.intelligence.agents import RagSemanticScoringBase
from app.intelligence.agents import RagSemanticScoringType
from app.intelligence.tracing import current_tracing_service


class RagSemanticScoringTextTiling(RagSemanticScoringBase):
    """Prices cuts the way TextTiling finds topic boundaries (Hearst). Cutting costs a
    fixed fee plus cut_weight · (1 − depth), where depth is how far the similarity of
    the window_sentences on either side dips below the peaks around it, less
    paragraph_discount at a blank line. Extending a chunk costs extend_weight · (1 −
    gain), where gain is how much the sentence lengthens the summed unit embedding of
    its chunk: a sentence on the chunk's topic adds nearly 1, one off it far less."""

    def __init__(self, embeddings: ModelEmbeddings, chunk_chars: int, window_sentences: int = 3,
        extend_weight: float = 1.0, cut_weight: float = 1.0, cut_fee: float = 1.2,
        paragraph_discount: float = 0.8) -> None:
        super().__init__(embeddings, chunk_chars)
        if window_sentences < 1:
            raise ValueError("The window must hold at least one sentence.")
        if min(extend_weight, cut_weight, cut_fee, paragraph_discount) < 0:
            raise ValueError("Weights, the cut fee and the paragraph discount cannot be negative.")

        self._window_sentences: int = window_sentences
        self._extend_weight: float = extend_weight
        self._cut_weight: float = cut_weight
        self._cut_fee: float = cut_fee
        self._paragraph_discount: float = paragraph_discount

    @property
    def scoring_type(self) -> RagSemanticScoringType:
        return RagSemanticScoringType.TEXT_TILING

    def score(self, units: list[str]) -> tuple[list[float], dict[tuple[int, int], float]]:
        with current_tracing_service().step("Sentence embeddings", "embedding", {"sentences": len(units)}) as span:
            vectors = self._vectors(units)
            span["dimensions"] = len(vectors[0]) if vectors else 0
            span["detail"] = f"{len(vectors)} sentences embedded, {span['dimensions']} dimensions, scaled to unit length"
        lengths = [len(current_unit) for current_unit in units]
        return self._cut_costs(units, vectors), self._extend_costs(lengths, vectors)

    def _cut_costs(self, units: list[str], vectors: list[list[float]]) -> list[float]:
        count, window = len(units), self._window_sentences
        similarities = [0.0] * count
        for gap in range(1, count):
            left = [sum(values) for values in zip(*vectors[max(0, gap - window):gap])]
            right = [sum(values) for values in zip(*vectors[gap:gap + window])]
            norms = math.sqrt(sum(map(mul, left, left))) * math.sqrt(sum(map(mul, right, right)))
            similarities[gap] = sum(map(mul, left, right)) / norms if norms else 0.0

        costs = [0.0] * count
        depths = [0.0] * count
        paragraphs: list[int] = []
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
            depths[gap] = depth
            if paragraph:
                paragraphs.append(gap)

        gaps = similarities[1:]
        deepest = max(range(1, count), key = depths.__getitem__)
        current_tracing_service().record("Window similarity", "scoring", {
            "detail": f"{count - 1} gaps, mean similarity {sum(gaps) / len(gaps):.3f}, "
                f"deepest dip {depths[deepest]:.3f} before sentence {deepest + 1}",
            "window_sentences": window,
            "cut_weight": self._cut_weight,
            "cut_fee": self._cut_fee,
            "paragraph_discount": self._paragraph_discount,
            "similarities": rounded(similarities),
            "depths": rounded(depths),
            "cut_costs": rounded(costs),
            "paragraph_gaps": paragraphs,
            "similarity": describe_numbers(gaps),
            "depth": describe_numbers(depths[1:])
        })
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

        values = list(costs.values())
        current_tracing_service().record("Extend costs", "scoring", {
            "detail": f"{len(values)} ways to grow a chunk priced, mean cost {sum(values) / len(values):.3f}"
                if values else "no chunk can grow",
            "extend_weight": self._extend_weight,
            "pairs": len(values),
            "cost": describe_numbers(values)
        })
        return costs
