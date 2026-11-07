from pydantic import BaseModel, Field


class ToolEditFileInput(BaseModel):
    path: str = Field(
        description = "The file to change, relative to the workspace root — for example "
            "'src/sort.py'. It must already exist; write a new file with write_file."
    )
    old_text: str = Field(
        min_length = 1,
        description = "The exact text to replace, copied from the file — whole lines, with "
            "enough of them that it appears only once. Read the file first so it matches."
    )
    new_text: str = Field(
        description = "The text to put in its place. Empty to delete old_text."
    )
    replace_all: bool = Field(
        default = False,
        description = "Replace every occurrence of old_text instead of requiring exactly one — "
            "for renaming something used throughout the file."
    )
