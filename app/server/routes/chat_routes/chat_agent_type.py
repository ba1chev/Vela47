from enum import Enum


class ChatAgentType(str, Enum):
    """Enumerates the agents a message can be sent to — what the dropdown in the sidebar
    chooses between. The choice is made per message, not per conversation: both agents
    read the same stored turns, so a conversation can move from one to the other, and
    every answer is marked with the value of the agent that wrote it.

    DEEP plans, splits the work across subagents and merges their results. RAG answers
    from the user's own uploaded documents and cites them."""

    DEEP = "deep"
    RAG = "rag"
