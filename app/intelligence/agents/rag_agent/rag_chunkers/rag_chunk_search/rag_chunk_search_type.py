from enum import Enum


class RagChunkSearchType(str, Enum):
    """Enumerates the searches that choose where a document is cut once the cost of
    every possible cut and every possible extension of a chunk is known. A_STAR finds
    the cheapest cut of the whole document that keeps every chunk within its length
    limits, steered by the fewest cuts the text still left needs."""

    A_STAR = "a_star"
