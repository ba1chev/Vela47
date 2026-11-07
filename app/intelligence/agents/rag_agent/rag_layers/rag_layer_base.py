from abc import ABC, abstractmethod

from app.intelligence.agents import RagContext
from app.intelligence.agents import RagLayerType


class RagLayerBase(ABC):
    """Abstract base for every stage of a RagPipeline, with the same contract as
    OperationLayerBase: a layer reads the RagContext it is handed and writes the field
    it owns, and returns nothing. The uniform signature is what lets the pipeline run
    whatever sequence the policy resolved, and lets the trace show the stages of both
    agents in the same way."""

    @property
    @abstractmethod
    def layer_type(self) -> RagLayerType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def execute(self, context: RagContext) -> None:
        raise NotImplementedError("Must be implemented")
