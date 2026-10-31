from pydantic import BaseModel, Field


class ToolSearchFilesInput(BaseModel):
    query: str = Field(
        description = "Text to look for. Matched case-insensitively as a substring, so a "
            "function name, an error message or a bare keyword all work."
    )
