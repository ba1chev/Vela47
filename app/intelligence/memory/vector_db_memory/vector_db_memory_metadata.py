from pydantic import Field
from typing import Optional

from app.intelligence.memory import VectorDbMemorySource
from app.intelligence.messages import MessageImmutableModel


class VectorDbMemoryMetadata(MessageImmutableModel):
    """What is known about a vector besides the vector: where its text came from, the
    section of the document it sits in, the general topic it is closest to and the
    words that set it apart. Worked out once when the text is indexed and stored with
    it, so whatever reads a search result later gets it without another model call.

    Every field but source may be empty: a document without headings has no section,
    and a text too short to compare has no keywords."""

    source: VectorDbMemorySource = Field(
        description = "The document, chunk and span the vector's text was taken from."
    )
    section: Optional[str] = Field(
        default = None,
        description = "Path of the headings the text sits under, outermost first, joined by ' › '. "
            "None when the document has no heading above it."
    )
    topic: Optional[str] = Field(
        default = None,
        description = "The general topic whose embedding is closest to the vector, from the topic "
            "register. None when no register was consulted."
    )
    topic_score: Optional[float] = Field(
        default = None,
        description = "Cosine similarity between the vector and its topic. Comparable only between "
            "vectors of the same embedding model, so it is kept rather than cut at a threshold."
    )
    keywords: list[str] = Field(
        default_factory = list,
        description = "Words of this text that say best what it is about, closest in meaning to "
            "the text first, as the document writes them."
    )
