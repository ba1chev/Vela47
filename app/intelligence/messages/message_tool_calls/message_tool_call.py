from pydantic import Field
from typing import Any, Literal, Optional

from app.intelligence.messages.message_base.message_immutable_model import MessageImmutableModel


class MessageToolCall(MessageImmutableModel):
    """A single, successfully parsed tool invocation extracted from an AIMessage. Contains
    everything needed to dispatch the call: the tool name, validated arguments, and an ID
    that the resulting ToolMessage must echo back so the model can correlate request and
    response. Produced by the framework's output parser; never constructed by the model
    directly."""
    name: str = Field(
        description = "Exact name of the tool the model wants to invoke, as registered in the "
            "tool registry. Must match the tool's declared name character-for-character; "
            "a mismatch results in an InvalidToolCall instead."
    )
    args: dict[str, Any] = Field(
        description = "Keyword arguments to pass to the tool, parsed from the model's JSON output. "
            "Keys and value types must conform to the tool's input schema; validation happens "
            "before execution and failures are captured as InvalidToolCall entries."
    )
    id: Optional[str] = Field(
        default = None,
        description = "Unique identifier generated for this tool call, used to match it with the "
            "ToolMessage that carries the result. When None, the framework assigns one before "
            "dispatching the call."
    )
    type: Literal["tool_call"] = "tool_call"
