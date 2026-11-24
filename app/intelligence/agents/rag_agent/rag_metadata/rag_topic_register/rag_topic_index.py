import math
from typing import Any
from operator import mul

from app.intelligence.agents import decode_topic_vector


class RagTopicIndex:
    """The topic register read for one embedding model: every topic's vector for that
    model, decoded and scaled to unit length once, so nearest() is a dot product per
    topic. A chunk's vector only compares with vectors of the model that made it, which
    is why the index is built for a model name and refuses a register that lacks it.

    Nothing is embedded here — the register already holds the vectors — so building
    one costs no model call and the server can build it at startup."""

    def __init__(self, register: dict[str, dict[str, Any]], model_name: str) -> None:
        missing = [current_topic for current_topic, current in register.items() if model_name not in current["vectors"]]
        if not register or missing:
            raise ValueError(
                f"The topic register lacks vectors of '{model_name}' for {len(missing)} of its "
                f"{len(register)} topics."
            )

        self._model_name: str = model_name
        self._topics: list[str] = list(register)
        self._vectors: list[list[float]] = [
            self._unit(decode_topic_vector(register[current_topic]["vectors"][model_name]))
            for current_topic in self._topics
        ]
        if len({len(current_vector) for current_vector in self._vectors}) != 1:
            raise ValueError(f"The vectors of '{model_name}' in the topic register differ in length.")

    @property
    def model_name(self) -> str:
        return self._model_name

    def _unit(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(map(mul, vector, vector))) or 1.0
        return [value / norm for value in vector]

    def nearest(self, vector: list[float]) -> tuple[str, float]:
        if len(vector) != len(self._vectors[0]):
            raise ValueError(
                f"A vector of {len(vector)} dimensions cannot be compared with the "
                f"{len(self._vectors[0])} of '{self._model_name}'."
            )

        unit = self._unit(vector)
        similarities = [sum(map(mul, unit, current_vector)) for current_vector in self._vectors]
        best = max(range(len(similarities)), key = similarities.__getitem__)
        return self._topics[best], similarities[best]

    def __len__(self) -> int:
        return len(self._topics)
