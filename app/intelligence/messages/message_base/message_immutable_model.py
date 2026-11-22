from pydantic import BaseModel


class MessageImmutableModel(BaseModel):
    """Shared pydantic base that enables frozen (immutable) instances across all models
    in the framework. Mutations after construction raise a ValidationError instead of
    silently corrupting state. Freezing alone does not make an instance hashable: a
    model with a dict or list field, as every message has, still cannot be a dictionary
    key or a set member."""

    model_config = {"frozen": True}
