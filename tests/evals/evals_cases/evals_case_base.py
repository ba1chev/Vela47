from pydantic import BaseModel, Field


class EvalsCaseBase(BaseModel):
    """Abstract base for one thing an agent is evaluated on. Every case is named, and
    the name is what ties a record — and a line of an eval session's summary — back to
    the case that produced it. Cases are frozen: they are the fixed ground an agent is
    measured against, before and after a change."""

    model_config = {"frozen": True}

    id: str = Field(
        description = "Short, stable name of the case, written into every record it produces "
            "and every summary line, so runs of the same case can be compared across sessions."
    )
