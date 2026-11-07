from pydantic import BaseModel, Field


class ToolListFilesInput(BaseModel):
    path: str = Field(
        default = ".",
        description = "Directory to list, relative to the workspace root. Leave it out to list "
            "the whole workspace."
    )
    depth: int = Field(
        default = 3,
        ge = 1,
        le = 8,
        description = "How many directory levels to show below path. Deeper directories are "
            "summarised by how many files they hold."
    )
