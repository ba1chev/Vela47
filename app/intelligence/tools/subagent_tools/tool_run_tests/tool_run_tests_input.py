from typing import Optional
from pydantic import BaseModel, Field


class ToolRunTestsInput(BaseModel):
    path: Optional[str] = Field(
        default = None,
        description = "A test file or directory to run, relative to the workspace root — for "
            "example 'tests/test_sort.py'. Leave it out to run every test in the workspace."
    )
    keyword: Optional[str] = Field(
        default = None,
        description = "Only run the tests whose name matches this pytest -k expression. Leave "
            "it out — the usual case — to run every test."
    )
