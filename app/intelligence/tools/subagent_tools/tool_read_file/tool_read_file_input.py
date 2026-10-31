from pydantic import BaseModel, Field


class ToolReadFileInput(BaseModel):
    path: str = Field(
        description = "Path of the file to read, relative to the workspace root — for "
            "example 'src/sort.py'. Paths that point outside the workspace are refused."
    )