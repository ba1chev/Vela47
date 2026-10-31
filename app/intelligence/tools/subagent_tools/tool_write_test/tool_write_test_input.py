from pydantic import BaseModel, Field


class ToolWriteTestInput(BaseModel):
    path: str = Field(
        description = "Name for the test file, for example 'test_sort.py'. It is placed "
            "under the tests directory and given a 'test_' prefix if it lacks one, so a "
            "runner can discover it."
    )
    content: str = Field(
        description = "The complete test file. Write real, runnable assertions against "
            "concrete inputs and expected outputs — not a description of what should "
            "be tested."
    )
