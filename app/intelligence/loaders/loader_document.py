from typing import Optional
from pydantic import BaseModel, Field

from app.intelligence.loaders import LoaderType


class LoaderDocument(BaseModel):
    """What a loader extracted from a file: its text, ready to be chunked or read by an
    agent, and the title the file gives itself when it has one. The title is kept apart
    from the text because callers use it differently — a page fetched by URL is listed
    under its <title> rather than under the URL, while the text is what gets searched."""

    model_config = {"frozen": True}

    text: str = Field(
        description = "The readable text of the file, with paragraphs separated by blank lines "
            "and headings, list items and table rows kept on lines of their own, so a chunker "
            "that follows paragraphs cuts it where the author did."
    )
    title: Optional[str] = Field(
        default = None,
        description = "The title the file declares for itself — an HTML <title>, a PDF's or a "
            "Word document's metadata title. None when it declares none."
    )
    loader_type: LoaderType = Field(
        description = "Which loader produced the text, so a caller can tell a page from a PDF "
            "without looking at the bytes again."
    )
