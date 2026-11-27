from pydantic import BaseModel, Field, field_validator


class RenameChatSessionRequest(BaseModel):
    """The body of a request to give a conversation a title of the owner's choosing. The
    title is flattened to one line the way an automatic title is, so a pasted newline or
    a run of spaces never reaches the list, and a title of only whitespace is refused
    rather than stored as an empty name."""

    title: str = Field(
        max_length = 200,
        description = "New title of the conversation, 1-200 characters once its whitespace is "
            "collapsed."
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, title: str) -> str:
        flattened = " ".join(title.split())

        if not flattened:
            raise ValueError("A title needs at least one visible character.")
        return flattened
