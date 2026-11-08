from typing import Optional
from pydantic import BaseModel, Field


class EvalsRecordBase(BaseModel):
    """Abstract base for what one run of an eval case measurably did. Every record says
    which case and which run it is, how long the agent took, and whether it crashed —
    a crash is recorded, not raised, because one broken run among three is information
    about the agent, while an exception would end the session.

    Records are frozen and plain data, so a session can write them as JSON lines and the
    judge can read them back later without running anything."""

    model_config = {"frozen": True}

    case: str = Field(
        description = "Id of the case the run was made for."
    )
    run: int = Field(
        ge = 0,
        description = "Which run of the case this is, counting from 0 within one session."
    )
    elapsed: float = Field(
        ge = 0,
        description = "Seconds the agent took to answer, without the runner's own setup."
    )
    crashed: Optional[str] = Field(
        default = None,
        description = "The exception the run ended with, as 'Type: message'. None when it finished."
    )
