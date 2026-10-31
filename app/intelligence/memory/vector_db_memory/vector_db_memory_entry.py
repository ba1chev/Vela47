from pydantic import Field

from app.intelligence.messages.message_base.message_base import MessageBase
from app.intelligence.messages.message_base.message_immutable_model import MessageImmutableModel


class VectorDbMemoryEntry(MessageImmutableModel):
    """Pairs a MessageBase with its dense vector embedding so the two can be
    stored and retrieved together. The message field holds the original content
    and metadata; the vector field holds the floating-point representation
    produced by ModelEmbeddings. Immutable by design — embeddings are computed
    once at insertion time and never updated in place."""

    message: MessageBase = Field(
        description = "The original message whose text was embedded. Carries the full "
            "content, role type, and metadata as stored in the conversation history."
    )
    vector: list[float] = Field(
        description = "Dense embedding of the message content as produced by ModelEmbeddings. "
            "Dimensionality is model-dependent and fixed for a given embedding model. "
            "Used by vector operations such as SEARCH to compute similarity scores."
    )
