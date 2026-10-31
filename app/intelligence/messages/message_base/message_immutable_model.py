from pydantic import BaseModel


class MessageImmutableModel(BaseModel):
    """Shared pydantic base that enables frozen (immutable) instances across all models
    in the framework. Inheriting from this class makes every instance hashable and safe
    to use as a dictionary key or in sets — mutations after construction raise a
    ValidationError instead of silently corrupting state."""

    model_config = {"frozen": True}
