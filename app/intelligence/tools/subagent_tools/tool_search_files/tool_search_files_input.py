from typing import Optional
from pydantic import BaseModel, Field


class ToolSearchFilesInput(BaseModel):
    query: str = Field(
        min_length = 1,
        description = "Text to look for. Matched case-insensitively as a substring, so a "
            "function name, an error message or a bare keyword all work."
    )
    path_glob: Optional[str] = Field(
        default = None,
        description = "Only search files whose path matches this pattern — for example '*.py' "
            "or 'tests/*'. A pattern without a slash is matched against the file name alone. "
            "Leave it out to search every file."
    )
    is_regex: bool = Field(
        default = False,
        description = "Treat query as a Python regular expression instead of plain text — for "
            "example 'def (quick|merge)_sort'. Still case-insensitive."
    )
