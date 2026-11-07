import re
import math
from typing import TypeVar

TOKEN_PATTERN = re.compile(r"\w+")

T = TypeVar("T")


def cosine_similarity(left_vector: list[float], right_vector: list[float]) -> float:
    dot_product = sum(
        current_number_left * current_number_right 
        for current_number_left, current_number_right
        in zip(left_vector, right_vector)
    )
    normalized_left_vector = math.sqrt(
        sum(current_number * current_number for current_number in left_vector)
    )
    normalized_right_vector = math.sqrt(
        sum(current_number * current_number for current_number in right_vector)
    )
    if normalized_left_vector == 0.0 or normalized_right_vector == 0.0:
        return 0.0
    return dot_product / (normalized_left_vector * normalized_right_vector)


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def reciprocal_rank_fusion(rankings: list[list[T]], rank_constant: int = 60) -> list[T]:
    scores: dict[int, float] = {}
    items: dict[int, T] = {}

    for current_ranking in rankings:
        for position, current_item in enumerate(current_ranking, start = 1):
            key = id(current_item)
            items[key] = current_item
            scores[key] = scores.get(key, 0.0) + 1.0 / (rank_constant + position)

    return [items[current_key] for current_key in sorted(scores, key = scores.get, reverse = True)]
