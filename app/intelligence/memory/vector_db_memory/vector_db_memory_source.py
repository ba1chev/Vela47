from pydantic import Field
from typing import Optional

from app.intelligence.messages import MessageImmutableModel


class VectorDbMemorySource(MessageImmutableModel):
    """Where the text behind a vector came from: which document, which of its chunks,
    and the exact span of the document's text the chunk is. The text itself is the
    entry's message content; this says where to find it again.

    The span is what lets a reader widen a passage after it was found — its neighbours
    are the chunks whose spans touch it — without the document being stored whole."""

    document_id: str = Field(
        min_length = 1,
        description = "Id of the document the chunk was cut from."
    )
    title: str = Field(
        description = "Title the document is listed and cited under."
    )
    chunk_index: int = Field(
        ge = 0,
        description = "Position of the chunk within its document, from 0."
    )
    start: Optional[int] = Field(
        default = None,
        ge = 0,
        description = "Offset in the document's text where the chunk begins. None when the chunk "
            "is not a verbatim slice of the text and so has no place in it."
    )
    end: Optional[int] = Field(
        default = None,
        ge = 0,
        description = "Offset in the document's text just past the chunk's last character. None "
            "exactly when start is."
    )
