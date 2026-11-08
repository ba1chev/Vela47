from abc import ABC, abstractmethod

from app.intelligence.sandbox import SandboxEnv
from app.intelligence.messages import MessageBase


class OperationSubagentProbeBase(ABC):
    """Abstract base for a check the system makes on a subagent's step — not something
    the subagent says it did, but something the system looks up for itself: the files in
    the workspace, a test run, the tool calls the subagent actually made.

    A subagent's report is the model's account of its own work, and a small model's
    account drifts from it: tests reported as passing that never ran, files reported as
    written that were not. Each fact a probe returns travels with the report to the
    merging layer, which is told to trust the fact where the two disagree.

    A probe is bound to the sandbox of one task, as a tool is, and lives for that task
    only. before() runs when the subagent starts, for a probe that compares — the
    workspace as it was — and after() when it has finished, with every message of its
    run. A probe that cannot check something says so in its fact rather than raising."""

    def __init__(self, sandbox_env: SandboxEnv) -> None:
        self._sandbox_env: SandboxEnv = sandbox_env

    def before(self) -> None:
        return None

    @abstractmethod
    def after(self, messages: list[MessageBase]) -> list[str]:
        raise NotImplementedError("Must be implemented")
