import math


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