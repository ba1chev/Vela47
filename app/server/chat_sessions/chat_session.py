from uuid import uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field, SerializeAsAny

from app.intelligence.messages import MessageBase
from app.server.security import format_chat_session_vrn


class ChatSession(BaseModel):
    """One conversation and everything said in it, owned by the entity that started it —
    the unit the server will hand out per user once sessions are wired in. It is a plain
    record: who owns it, what it is called, and the ordered turns, kept in the
    framework's own message types so an agent can be resumed from it without a
    translation layer in between.

    Messages are declared as MessageBase and serialised as whatever they really are, so
    an AI message keeps its tool calls and token usage when the session is dumped. They
    are accepted only as message instances. Turning stored JSON back into messages is
    the store's job, done through MessageFactory, because the message models cannot
    validate their own JSON: their type field accepts the MessageType member but not its
    string value.

    Frozen like the entity and policy models — a changed conversation is a new record,
    and the store is where a change becomes durable.

    Its VRN puts the owner in the owner segment, which is what lets one statement in
    the user role — vrn:session:${principal.id}:* — grant each caller its own
    conversations and nothing else."""

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
