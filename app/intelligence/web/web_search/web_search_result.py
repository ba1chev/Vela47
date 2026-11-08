from pydantic import BaseModel, Field


class WebSearchResult(BaseModel):
    """One hit from a web search: enough to decide whether the page is worth fetching,
    and the URL to fetch it with."""

    model_config = {"frozen": True}

    title: str = Field(description = "The page's title as the search engine shows it.")
    url: str = Field(description = "Direct link to the page — never a search engine's redirect link.")
    snippet: str = Field(
        default = "",
        description = "The search engine's excerpt of the page around the query's words. A "
            "hint of what the page says, not a quote to rely on — fetch the page for that."
    )
