from pydantic import BaseModel, Field


class UploadKnowledgeRequest(BaseModel):
    """The body of a document upload. The browser reads the file and sends its text, so
    the server receives what it will index and nothing it would first have to decode —
    plain text and Markdown today. The size limits are the configuration's, checked by
    the route against the encoded size; the max_length here is only a backstop against a
    body no limit could ever allow."""

    title: str = Field(
        min_length = 1,
        max_length = 200,
        description = "Name the document is listed and cited under, normally its file name."
    )
    content: str = Field(
        min_length = 1,
        max_length = 20_000_000,
        description = "The document's full text."
    )
