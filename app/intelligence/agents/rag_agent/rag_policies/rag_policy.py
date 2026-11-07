from abc import ABC, abstractmethod

from app.intelligence.agents import RagLayerBase
from app.intelligence.agents import RagLayersFactoryBase


class RagPolicy(ABC):
    """Decides which layers a RagPipeline runs and in what order, and supplies each one
    its dependencies — the RAG counterpart of OperationPolicy. The factory is passed in
    rather than held, so a policy names layer types and never imports a concrete layer,
    and the pipeline that runs the sequence never learns how it was chosen."""

    @abstractmethod
    def resolve(self, factory: RagLayersFactoryBase) -> list[RagLayerBase]:
        raise NotImplementedError("Must be implemented")
