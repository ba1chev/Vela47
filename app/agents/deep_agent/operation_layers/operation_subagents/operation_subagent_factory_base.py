from abc import ABC, abstractmethod

from app.agents.deep_agent.operation_layers.operation_subagents.operation_subagent import OperationSubagent
from app.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_type import OperationSubagentType


class OperationSubagentFactoryBase(ABC):
    """Abstract factory for OperationSubagent instances. The subagents layer
    depends on this rather than on a concrete factory so a test can hand it a
    factory returning stubbed agents, and so the set of supported subagent types
    can change without touching the layer."""

    @abstractmethod
    def create(self, type: OperationSubagentType) -> OperationSubagent:
        raise NotImplementedError("Must be implemented")
