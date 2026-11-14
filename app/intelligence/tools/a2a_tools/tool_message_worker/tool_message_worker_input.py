from pydantic import BaseModel, Field


class ToolMessageWorkerInput(BaseModel):
    message: str = Field(
        min_length = 1,
        description = "What to tell the other worker — for a bug, the file and function, the "
            "input, and the expected and the actual result."
    )
