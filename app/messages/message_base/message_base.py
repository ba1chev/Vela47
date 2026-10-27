from pydantic import Field
from abc import ABC, abstractmethod
from typing import Any, Optional, Union

from app.messages.message_type import MessageType
from app.messages.message_base.message_immutable_model import MessageImmutableModel

ContentPart = Union[str, dict[str, Any]]


class MessageBase(MessageImmutableModel, ABC):
    """Abstract base for every message in a conversation. Defines the common envelope —
    content, role type, optional metadata, and identity — that all concrete message types
    share. Cannot be instantiated directly; subclasses must implement __str__ and declare
    a Literal MessageType so the framework can route and serialise messages without
    resorting to isinstance checks."""
    content: Union[str, list[ContentPart]] = Field(
        description = "The body of the message. Accepts either a plain string for text-only "
            "exchanges or a list of content blocks for multimodal input — each block is a dict "
            "with a 'type' key (e.g. 'text', 'image_url') and the corresponding payload. "
            "All concrete subclasses share this field."
    )
    type: MessageType = Field(
        description = "Role tag that identifies who produced this message. Each concrete subclass "
            "locks this to a Literal value (MessageType.HUMAN_MESSAGE, MessageType.AI_MESSAGE, …), "
            "which lets the model router and serialisers dispatch on type without isinstance checks."
    )
    additional_kwargs: dict[str, Any] = Field(
        default_factory = dict,
        description = "Escape hatch for provider-specific parameters that have no first-class field "
            "here — e.g. Ollama's 'images' list or vendor-specific headers. These are forwarded "
            "verbatim to the underlying API call and are ignored by the rest of the framework."
    )
    response_metadata: dict[str, Any] = Field(
        default_factory = dict,
        description = "Metadata attached by the model after generation — finish reason, model name, "
            "server-side latency, logprobs, and similar diagnostics. Populated only on messages "
            "that originate from a model response; empty for outgoing messages."
    )
    id: Optional[str] = Field(
        default = None,
        description = "Stable identifier for this message, useful when storing conversations in a "
            "database or reconciling streamed chunks. Assigned by the caller or the framework; "
            "None means the message has not been assigned an ID yet."
    )
    name: Optional[str] = Field(
        default = None,
        description = "Human-readable label for the sender — e.g. a username or agent name. "
            "Passed through to the model as-is when set, which some providers use to distinguish "
            "between multiple participants in the same role."
    )

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError("Must be implemented")
