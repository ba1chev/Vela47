from enum import Enum


class ModelClientType(str, Enum):
    """Enumerates the backends a model can be served by. OLLAMA is a local Ollama
    server, what development runs on; BEDROCK is Amazon Bedrock, what production calls
    with the IAM role of its task, so no machine of its own has to hold a GPU."""

    OLLAMA = "ollama"
    BEDROCK = "bedrock"
