from abc import ABC, abstractmethod

from app.agents.deep_agent.operation_context import OperationContext
from app.agents.deep_agent.operation_layers.operation_layer_type import OperationType


class OperationLayerBase(ABC):
    """Abstract base for every stage of an OperationPipeline. Layers communicate
    exclusively through the OperationContext they are handed: each reads the
    fields its predecessors filled and writes the one it owns, which is why
    execute() returns nothing. Keeping the signature uniform is what lets the
    pipeline run any sequence of layers the policy resolves without knowing what
    each one does, and what lets a late layer such as merging still reach the
    original goal rather than only its predecessor's output."""

    @property
    @abstractmethod
    def operation_type(self) -> OperationType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def execute(self, context: OperationContext) -> None:
        raise NotImplementedError("Must be implemented")
