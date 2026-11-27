from typing import Any, Sequence

TRACE_DIGITS = 4


def rounded(values: Sequence[float], digits: int = TRACE_DIGITS) -> list[float]:
    return [round(current_value, digits) for current_value in values]


def describe_numbers(values: Sequence[float], digits: int = TRACE_DIGITS) -> dict[str, Any]:
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "min": round(min(values), digits),
        "mean": round(sum(values) / len(values), digits),
        "max": round(max(values), digits)
    }
