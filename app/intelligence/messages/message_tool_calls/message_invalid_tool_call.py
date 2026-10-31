from pydantic import Field
from typing import Literal, Optional

from app.intelligence.messages.message_base.message_immutable_model import MessageImmutableModel


class MessageInvalidToolCall(MessageImmutableModel):
    """A tool invocation the model attempted but that the output parser could not turn into
    a valid ToolCall — typically because the JSON was malformed, the tool name was unknown,
    or the arguments failed schema validation. All fields are Optional because the degree
    of parseability varies. Kept alongside tool_calls in AIMessage so the application can
    log, retry, or return an informative error to the model."""
    name: Optional[str] = Field(
        default = None,
        description = "Tool name the model attempted to call, if it could be extracted from the "
            "raw output. None means the model's output was so malformed that even the name "
            "could not be recovered."
    )
    args: Optional[str] = Field(
        default = None,
        description = "Raw, unparsed arguments string exactly as the model produced it — preserved "
            "for debugging and retry logic. None when no argument payload was present at all."
    )
    id: Optional[str] = Field(
        default = None,
        description = "Tool call ID from the model's output, if present. Allows correlating this "
            "failed attempt with a ToolMessage error reply when the application decides to "
            "return an explicit error to the model."
    )
    error: Optional[str] = Field(
        default = None,
        description = "Human-readable description of what went wrong — e.g. 'JSON parse error', "
            "'unknown tool name', or a schema validation message. Intended for logging and for "
            "constructing informative error ToolMessages."
    )
    type: Literal["invalid_tool_call"] = "invalid_tool_call"
