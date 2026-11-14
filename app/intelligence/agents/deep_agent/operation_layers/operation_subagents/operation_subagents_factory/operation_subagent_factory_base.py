from typing import Optional
from abc import ABC, abstractmethod

from app.intelligence.sandbox import SandboxEnv
from app.intelligence.tools import ToolMessageWorker
from app.intelligence.agents import OperationSubagent
from app.intelligence.agents import OperationSubagentType


class OperationSubagentFactoryBase(ABC):
    """Abstract factory for OperationSubagent instances. The subagents layer
    depends on this rather than on a concrete factory so a test can hand it a
    factory returning stubbed agents, and so the set of supported subagent types
    can change without touching the layer. peer_tool, when given, reaches an earlier
    subagent of the run (see OperationSubagentPeering)."""

    @abstractmethod
    def create(self, type: OperationSubagentType, sandbox_env: SandboxEnv,
        peer_tool: Optional[ToolMessageWorker] = None) -> OperationSubagent:
        raise NotImplementedError("Must be implemented")
