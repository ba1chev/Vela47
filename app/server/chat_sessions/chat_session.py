from uuid import uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field, SerializeAsAny

from app.intelligence.messages import MessageBase
from app.server.security import format_chat_session_vrn


class ChatSession(BaseModel):
    """One conversation and everything said in it, owned by the entity that started it,
    with its turns kept as the framework's own message types so an agent resumes from it
    directly. Messages are serialised as what they really are, so an AI message keeps
    its tool calls and usage; rebuilding them from JSON is the store's job, through
    MessageFactory, because the message models cannot validate their own JSON.

    Frozen: a changed conversation is a new record. Its VRN carries the owner, which
    lets one statement, vrn:session:${principal.id}:*, grant each caller its own
    conversations only."""

    model_config = {"frozen": True}

    id: str = Field(
        default_factory = lambda: uuid4().hex,
        description = "Random hex id of the conversation, generated at creation."
    )
    owner_id: str = Field(
        min_length = 1,
        description = "Id of the entity the conversation belongs to — a stored admin or user, or "
            "a guest, whose id exists only inside its session token."
    )
    title: str = Field(
        default = "New chat",
        min_length = 1,
        max_length = 200,
        description = "Human-readable title shown in the list of conversations."
    )
    messages: list[SerializeAsAny[MessageBase]] = Field(
        default_factory = list,
        description = "The turns in the order they happened. Raw tool artifacts are never part "
            "of a stored conversation, so a message read back from a store carries none."
    )
    created_at: datetime = Field(
        default_factory = lambda: datetime.now(timezone.utc),
        description = "When the conversation was started, in UTC."
    )
    updated_at: datetime = Field(
        default_factory = lambda data: data["created_at"],
        description = "When a message was last appended, in UTC. Equal to created_at until then, "
            "and what orders an owner's conversations newest first."
    )

    @property
    def vrn(self) -> str:
        return format_chat_session_vrn(self.owner_id, self.id)
