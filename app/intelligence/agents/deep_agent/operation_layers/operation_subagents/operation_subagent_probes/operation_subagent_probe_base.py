from abc import ABC, abstractmethod

from app.intelligence.sandbox import SandboxEnv
from app.intelligence.messages import MessageBase


class OperationSubagentProbeBase(ABC):
    """Abstract base for a check the system makes on a subagent's step itself (the files
    in the workspace, a test run, the tool calls actually made) rather than taking the
    model's word for it. Each fact travels with the report to merging, which trusts the
    fact where the two disagree.

    A probe is bound to one task's sandbox. before() runs when the subagent starts,
    after() when it has finished, with every message of its run. A probe that cannot
    check something says so in its fact rather than raising."""

    def __init__(self, sandbox_env: SandboxEnv) -> None:
        self._sandbox_env: SandboxEnv = sandbox_env

    def before(self) -> None:
        return None

    @abstractmethod
    def after(self, messages: list[MessageBase]) -> list[str]:
        raise NotImplementedError("Must be implemented")
