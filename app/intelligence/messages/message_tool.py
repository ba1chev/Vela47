from pydantic import Field
from typing import Any, Literal, Optional

from app.intelligence.messages.message_type import MessageType
from app.intelligence.messages.message_base.message_base import MessageBase


class MessageTool(MessageBase):
    """Carries the result of a tool execution back into the conversation so the model
    can incorporate it into its next response. Linked to the triggering AIMessage via
    tool_call_id. The status field signals whether execution succeeded or failed, letting
    the model decide how to recover. The artifact field holds the raw Python object produced
    by the tool — it never reaches the model prompt; only content does."""
    type: Literal[MessageType.TOOL_MESSAGE] = MessageType.TOOL_MESSAGE
    tool_call_id: str = Field(
        description = "ID that ties this result back to the ToolCall that triggered it. "
            "Must exactly match the 'id' field of the corresponding ToolCall in the preceding "
            "AIMessage so the model can correlate the invocation with its outcome."
    )
    status: Literal["success", "error"] = Field(
        default = "success",
        description = "Outcome of the tool execution. 'success' means the content field holds a "
            "usable result; 'error' means it holds an error description. The model sees this "
            "flag and can decide whether to retry, use a fallback tool, or inform the user."
    )
    artifact: Optional[Any] = Field(
        default = None,
        description = "Raw object produced by the tool execution — e.g. a pandas DataFrame, a "
            "Pillow image, or binary bytes — kept for downstream pipeline steps. This field is "
            "never serialised into the prompt; only 'content' reaches the model."
    )

    model_config = {"frozen": False}

    def __str__(self) -> str:
        body = self.content if isinstance(self.content, str) else str(self.content)
        return f"Tool({self.tool_call_id}): {body}"
