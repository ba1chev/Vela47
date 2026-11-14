from app.intelligence.model import ModelClientType
from app.intelligence.model import ModelClientBase
from app.intelligence.model import ModelClientOllama
from app.intelligence.model import ModelClientBedrock


MODEL_CLIENTS_REGISTRY: dict[ModelClientType, type[ModelClientBase]] = {
    ModelClientType.OLLAMA: ModelClientOllama,
    ModelClientType.BEDROCK: ModelClientBedrock
}
