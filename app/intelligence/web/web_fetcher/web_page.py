from typing import Optional
from pydantic import BaseModel, Field


class WebPage(BaseModel):
    """What a fetch brought back: the bytes of the final response after redirects, and
    what the server said they are. Bytes rather than text, because deciding how to read
    them — as a page, a PDF, a Word document — is a loader's job and depends on
    content_type, which a decoded string would already have lost."""

    model_config = {"frozen": True}

    url: str = Field(
        description = "The URL the content finally came from, after following redirects — the "
            "one to cite, which may differ from the one asked for."
    )
    status_code: int = Field(
        description = "HTTP status of the final response. Always below 400: an error status is "
            "raised as WebAccessError rather than returned."
    )
    content_type: str = Field(
        default = "",
        description = "Media type from the Content-Type header, lower case and without "
            "parameters — 'text/html', 'application/pdf'. Empty when the server sent none."
    )
    encoding: Optional[str] = Field(
        default = None,
        description = "Charset declared in the Content-Type header, if any. Passed on to the "
            "loader, which otherwise looks for one in the content itself."
    )
    content: bytes = Field(
        description = "The response body, decompressed, cut at the fetcher's size limit."
    )
    truncated: bool = Field(
        default = False,
        description = "True when the body was longer than the size limit and was cut. The text "
            "is still usable, but whoever reads it should know it ends early."
    )
