from typing import Optional
from pydantic import BaseModel, Field


class ToolReadFileInput(BaseModel):
    path: str = Field(
        description = "Path of the file to read, relative to the workspace root — for "
            "example 'src/sort.py'. Paths that point outside the workspace are refused."
    )
    start_line: int = Field(
        default = 1,
        ge = 1,
        description = "First line to return, counting from 1. Leave it out to start at the top; "
            "set it to continue a long file from where the previous read stopped."
    )
    end_line: Optional[int] = Field(
        default = None,
        ge = 1,
        description = "Last line to return, inclusive. Leave it out to read as far as one call "
            "allows."
    )
