from pydantic import BaseModel, Field


class RagRelevanceScore(BaseModel):
    """The reranker's verdict on one passage. The passage is named by the number it was
    shown under rather than by its id, because a small model reliably repeats a number
    and does not reliably repeat a 40-character id."""

    index: int = Field(
        ge = 1,
        description = "Number of the passage, exactly as it was shown in the list, starting at 1."
    )
    score: int = Field(
        ge = 0,
        le = 10,
        description = "How well the passage answers the query: 10 answers it directly, 5 is on the "
            "subject without answering, 0 is unrelated."
    )
