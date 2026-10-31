from enum import Enum


class ModelType(Enum):
    """Classifies model instances by their primary capability. Used to route
    requests to the correct model implementation without resorting to isinstance
    checks — FOUNDATION handles text generation, EMBEDDINGS handles vector
    representations."""

    FOUNDATION = 1
    EMBEDDINGS = 2
