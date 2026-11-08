from pydantic import BaseModel, Field


class ToolFetchUrlInput(BaseModel):
    url: str = Field(
        min_length = 1,
        description = "The full address of the page or document to read, starting with "
            "https:// — for example a URL from a web_search result."
    )
    start_index: int = Field(
        default = 0,
        ge = 0,
        description = "Character position to start reading from. Leave it out for the start; "
            "use the value a previous call suggested to continue a long page."
    )
    max_length: int = Field(
        default = 4000,
        ge = 500,
        le = 12000,
        description = "How many characters of text to return in this call."
    )
