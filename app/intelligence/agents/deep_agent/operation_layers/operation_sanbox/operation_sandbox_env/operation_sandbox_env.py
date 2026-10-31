from abc import ABC, abstractmethod

from app.intelligence.agents.deep_agent.operation_layers.operation_sanbox.operation_sandbox_env.operation_sandbox_command_result import OperationSandboxCommandResult


class OperationSandboxEnv(ABC):
    """Where one subagent's tool operations actually take effect.

    The subagent itself never runs in here — its reasoning loop lives in the server
    process because that is what talks to the model. What the sandbox contains is the
    consequences of its tools: files it writes and commands it runs. Keeping that
    distinction is what lets a sandbox be swapped for a container without the agent,
    the layer, or the model call knowing anything changed.

    Every path a method receives originates from a model and is therefore untrusted.
    Implementations must confine it to the environment and refuse anything that
    escapes, rather than leaving that to the caller — a tool author who forgets the
    check should not be able to reach the host filesystem."""

    @property
    @abstractmethod
    def identifier(self) -> str:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def write_file(self, relative_path: str, content: str) -> str:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def read_file(self, relative_path: str) -> str:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def list_files(self) -> list[str]:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def run(self, command: str, timeout_seconds: int = 60) -> OperationSandboxCommandResult:
        raise NotImplementedError("Must be implemented")
