from enum import Enum


class VectorDBSearchType(Enum):
    """The two families of graph search. UNINFORMED algorithms know nothing about the
    goal beyond recognising it when they reach it; INFORMED ones are steered by a
    heuristic that estimates the remaining distance to the goal from any node."""

    UNINFORMED = 0
    INFORMED = 1
