from typing import Literal
from pydantic import Field

from app.intelligence.security import SecurityType
from app.intelligence.security import SecurityVerdict
from app.intelligence.security import SecurityPromptType


class SecurityPromptVerdict(SecurityVerdict):
    """The verdict of a prompt detector: what SecurityVerdict holds, with the threat the
    text was inspected for. It is a class of its own so the threat is typed by the
    family's enum rather than written as a plain string."""

    security_type: Literal[SecurityType.PROMPT] = SecurityType.PROMPT
    prompt_type: SecurityPromptType = Field(
        description = "The threat the text was inspected for, which also says where the text came "
            "from: the user's message, the result of a tool or stored content."
    )
