from typing import Optional, Self
from pydantic import BaseModel, Field, model_validator


class UploadKnowledgeRequest(BaseModel):
    """The body of a document upload. A text file arrives as its text in content, which
    is what the browser can read without help. A PDF or a Word document cannot be sent
    as text, so it arrives as its bytes in content_base64, with the media type the
    browser gave it; the server picks a loader from that type and the file's name and
    extracts the text itself. Exactly one of the two is sent.

    The size limits are the configuration's — the raw upload is checked against one and
    the extracted text against another, by the route. The max_length here is only a
    backstop against a body no limit could ever allow."""

    title: str = Field(
        min_length = 1,
        max_length = 200,
        description = "Name the document is listed and cited under, normally its file name. Its "
            "extension also tells the server how to read the file."
    )
    content: Optional[str] = Field(
        default = None,
        min_length = 1,
        max_length = 20_000_000,
        description = "The document's full text, for a file that is already text — plain text, "
            "Markdown, CSV, an HTML page."
    )
    content_base64: Optional[str] = Field(
        default = None,
        min_length = 1,
        max_length = 30_000_000,
        description = "The file's bytes, base64 encoded, for a file that is not text — a PDF or a "
            "Word document."
    )
    content_type: Optional[str] = Field(
        default = None,
        max_length = 200,
        description = "Media type the browser reported for the file, if any — 'application/pdf'. "
            "Used before the file name to choose how to read it."
    )

    @model_validator(mode = "after")
    def validate_one_content(self) -> Self:
        if (self.content is None) == (self.content_base64 is None):
            raise ValueError("Send the document either as content or as content_base64, not both or neither.")
        return self
