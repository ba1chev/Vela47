from pydantic import BaseModel, Field


class ToolWriteFileInput(BaseModel):
    path: str = Field(
        description = "Where to write, relative to the workspace root — for example "
            "'src/sort.py'. Missing parent directories are created. Paths pointing "
            "outside the workspace are refused."
    )
    content: str = Field(
        description = "The complete new contents of the file. This replaces the file "
            "entirely rather than appending, so include everything the file needs."
    )