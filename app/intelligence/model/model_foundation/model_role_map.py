from app.intelligence.messages.message_type import MessageType


MODEL_ROLE_MAP: dict[MessageType, str] = {
    MessageType.HUMAN_MESSAGE: "user",
    MessageType.SYSTEM_MESSAGE: "system",
    MessageType.AI_MESSAGE: "assistant",
    MessageType.TOOL_MESSAGE: "tool"
}