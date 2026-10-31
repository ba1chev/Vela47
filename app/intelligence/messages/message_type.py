from enum import Enum


class MessageType(Enum):
    """Enumerates the roles a message can occupy in a conversation. Each value is the
    string the model API expects as the role identifier, so the enum can be serialised
    directly without an extra mapping step."""
    
    HUMAN_MESSAGE = "human"
    SYSTEM_MESSAGE = "system"
    AI_MESSAGE = "ai"
    TOOL_MESSAGE = "tool"
