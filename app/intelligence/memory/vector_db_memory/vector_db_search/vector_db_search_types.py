from enum import Enum


class VectorDBSearchType(Enum):
    """The three families of search. UNINFORMED algorithms know nothing about the goal
    beyond recognising it when they reach it; INFORMED ones are steered by a heuristic
    that estimates the remaining distance to the goal. APPROXIMATE ones find the
    vectors nearest a query through an index built over them, trading exactness for
    not comparing the query with every vector."""

    UNINFORMED = 0
    INFORMED = 1
    APPROXIMATE = 2
