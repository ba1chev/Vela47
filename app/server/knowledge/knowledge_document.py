from uuid import uuid4
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from app.server.security import format_knowledge_document_vrn


class KnowledgeDocument(BaseModel):
    """One document a user uploaded for the RAG agent, as the rest of the server sees it
    — who owns it, what it is called, how big it was and how many chunks it became. Its
    text is not here: once indexed, a document exists for search only as its chunks,
    stored with their vectors and loaded by the store when a question needs them.

    Its VRN puts the owner in the owner segment, like a conversation's, which is what
    lets vrn:knowledge:${principal.id}:* grant each caller its own documents and nobody
    else's."""

    model_config = {"frozen": True}

    id: str = Field(
        default_factory = lambda: uuid4().hex,
        description = "Random hex id of the document. Prefixes the id of every one of its chunks."
    )
    owner_id: str = Field(
        min_length = 1,
        description = "Id of the entity the document belongs to — a stored admin or user, or a guest."
    )
    title: str = Field(
        min_length = 1,
        max_length = 200,
        description = "Name the document is listed and cited under, normally its file name."
    )
    size_bytes: int = Field(
        ge = 0,
        description = "Size of the uploaded text in UTF-8 bytes — what counts against the owner's limit."
    )
    chunk_count: int = Field(
        ge = 0,
        description = "How many chunks the document was cut into when it was indexed."
    )
    created_at: datetime = Field(
        default_factory = lambda: datetime.now(timezone.utc),
        description = "When the document was uploaded, in UTC."
    )

    @property
    def vrn(self) -> str:
        return format_knowledge_document_vrn(self.owner_id, self.id)
