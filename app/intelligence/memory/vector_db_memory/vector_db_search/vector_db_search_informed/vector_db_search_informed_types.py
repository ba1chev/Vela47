from enum import Enum


class VectorDBSearchInformedType(Enum):
    """The informed searches, all over a weighted graph and a heuristic. A_STAR and
    ITERATIVE_DEEPENING_A_STAR rank nodes by path cost plus heuristic; GREEDY, BEAM and
    HILL_CLIMBING by the heuristic alone, with BEAM and HILL_CLIMBING also bounding how
    many nodes are kept in the queue."""

    A_STAR_SEARCH = 0
    BEAM_SEARCH = 1
    GREEDY_SEARCH = 2
    HILL_CLIMBING = 3
    ITERATIVE_DEEPENING_A_STAR_SEARCH = 4
