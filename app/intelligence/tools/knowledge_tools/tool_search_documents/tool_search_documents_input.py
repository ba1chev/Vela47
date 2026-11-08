from pydantic import BaseModel, Field


class ToolSearchDocumentsInput(BaseModel):
    query: str = Field(
        min_length = 1,
        description = "What to look for in the user's documents — a question or the key terms "
            "of one. Exact names, codes and numbers are matched as words as well as by meaning."
    )
    top_k: int = Field(
        default = 4,
        ge = 1,
        le = 8,
        description = "How many passages to return, best first."
    )
