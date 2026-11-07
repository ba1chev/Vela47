from typing import Optional
from pydantic import BaseModel, Field


class ImportKnowledgeUrlRequest(BaseModel):
    """The body of a request to add a web page — or a PDF or Word document online — to the
    caller's documents. The server fetches it through the same guarded fetcher the
    agents use, so a URL pointing at a private address is refused here as well."""

    url: str = Field(
        min_length = 1,
        max_length = 2000,
        description = "Full address of the page or document, starting with http:// or https://."
    )
    title: Optional[str] = Field(
        default = None,
        min_length = 1,
        max_length = 200,
        description = "Name to list and cite it under. Left out, the page's own title is used, "
            "and its URL when it has none."
    )
