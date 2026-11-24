from typing import Self
from pydantic import BaseModel, Field, model_validator


class RagMetadataDocument(BaseModel):
    """A document at the moment its chunks have been embedded — everything metadata can
    be worked out from: the whole text, for what a chunk's surroundings say about it,
    and every chunk beside its vector, in the same order. Built by RagIndexer and read
    by every metadata extractor; none of them changes it."""

    model_config = {"frozen": True}

    document_id: str = Field(
        min_length = 1,
        description = "Id of the document, the prefix of every one of its chunk ids."
    )
    title: str = Field(
        description = "Title the document is listed and cited under."
    )
    text: str = Field(
        description = "The document's whole text, exactly as the chunker was given it."
    )
    chunks: list[str] = Field(
        description = "The chunks the document was cut into, in order."
    )
    vectors: list[list[float]] = Field(
        description = "The embedding of each chunk, in the same order as chunks."
    )

    @model_validator(mode = "after")
    def validate_one_vector_per_chunk(self) -> Self:
        if len(self.chunks) != len(self.vectors):
            raise ValueError("Every chunk needs exactly one vector.")
        return self
