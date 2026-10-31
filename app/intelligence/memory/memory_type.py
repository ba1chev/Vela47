from enum import Enum


class MemoryType(Enum):
    """Enumerates the kinds of store an agent can be given to remember with. Exists so
    a caller can name which one it wants without importing the concrete class, which is
    what allows the choice to be made in data — a config entry, a request field — rather
    than fixed in code at construction.

    SHORT_TERM_MEMORY is the ordered history of a single session and dies with it.
    VECTOR_DB_MEMORY outlives the session and is retrieved by meaning rather than by
    position, which is what makes it usable when the relevant turn is no longer recent."""

    SHORT_TERM_MEMORY = 0
    LONG_TERM_MEMORY = 1
    VECTOR_DB_MEMORY = 2