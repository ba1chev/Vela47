from pydantic import BaseModel, Field


class ToolWebSearchInput(BaseModel):
    query: str = Field(
        min_length = 1,
        description = "What to search the web for — a few specific keywords work better than a "
            "whole sentence."
    )
    max_results: int = Field(
        default = 6,
        ge = 1,
        le = 10,
        description = "How many results to return, best first."
    )
