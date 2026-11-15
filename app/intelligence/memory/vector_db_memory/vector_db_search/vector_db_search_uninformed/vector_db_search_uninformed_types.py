from enum import Enum


class VectorDBSearchUninformedType(Enum):
    """The uninformed searches. DEPTH_FIRST, BREADTH_FIRST, DEPTH_LIMITED and
    ITERATIVE_DEEPENING walk an unweighted graph and answer whether the goal is
    reachable; UNIFORM_COST walks a weighted one and returns the cheapest path."""

    DEPTH_FIRST_SEARCH = 0
    BREADTH_FIRST_SEARCH = 1
    UNIFORM_COST_SEARCH = 2
    DEPTH_LIMITED_SEARCH = 3
    ITERATIVE_DEEPENING_SEARCH = 4
