from enum import Enum


class RagChunkerType(str, Enum):
    """Enumerates the ways a document can be cut into chunks before it is embedded. The
    cut decides what retrieval can ever find: a chunk is the unit that gets a vector, so
    an answer split across two chunks is found by neither as well as it would be whole.

    SEMANTIC cuts between sentences where the topic changes, found by embedding every
    sentence, and is the default. RECURSIVE follows the document's own structure —
    paragraphs, then lines, then sentences, then words — without a model. FIXED cuts at a
    constant width whatever the structure, which suits text that has none, such as a log."""

    RECURSIVE = "recursive"
    FIXED = "fixed"
    SEMANTIC = "semantic"
