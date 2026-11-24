from enum import Enum


class RagMetadataType(str, Enum):
    """Enumerates what a RagMetadataAttacher works out about each chunk of a document.
    SECTION is the path of the headings above the chunk, read from the document's
    Markdown. TOPIC is the general topic whose embedding is closest to the chunk's,
    from the topic register. KEYWORDS are the chunk's words that stand out in its
    document and come closest to its meaning."""

    SECTION = "section"
    TOPIC = "topic"
    KEYWORDS = "keywords"
