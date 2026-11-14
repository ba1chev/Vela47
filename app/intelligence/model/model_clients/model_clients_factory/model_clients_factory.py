from typing import Any

from app.intelligence.model import ModelClientType
from app.intelligence.model import ModelClientBase
from app.intelligence.model import MODEL_CLIENTS_REGISTRY
from app.intelligence.model import ModelClientsFactoryBase


class ModelClientsFactory(ModelClientsFactoryBase):
    """Concrete factory that maps each ModelClientType to its ModelClientBase subclass
    and forwards the keyword arguments to it. A client holds no conversation, so one per
    process serves every model and every request.

    Registry reference:
      OLLAMA  -> ModelClientOllama()
      BEDROCK -> ModelClientBedrock(region_name=<region>)"""

    def create(self, type: ModelClientType, **kwargs: Any) -> ModelClientBase:
        cls = MODEL_CLIENTS_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No model client class registered for type '{type}'. "
                f"Known types: {list(MODEL_CLIENTS_REGISTRY)}"
            )

        return cls(**kwargs)
