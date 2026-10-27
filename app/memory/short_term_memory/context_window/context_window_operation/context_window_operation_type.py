from enum import Enum


class ContextWindowOperationType(Enum):
    """Enumerates the transformations that can be applied to the content of a
    ContextWindow. Each value names a distinct strategy — from structural
    re-sizing to semantic compression — that the operation pipeline can execute
    to keep the window within its capacity without losing critical context."""

    EXPAND = 1
    SHRINK = 2
    SLIDE = 3
    SUMMARIZE = 4
    TRUNCATE = 5
    FLATTEN = 6
