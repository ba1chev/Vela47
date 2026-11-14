from typing import Callable

from app.intelligence.tools import ToolBase
from app.intelligence.tools import ToolMessageWorkerInput


class ToolMessageWorker(ToolBase[ToolMessageWorkerInput, str]):
    """Sends a message to the worker that did an earlier step of the run and returns its
    answer — the one way a subagent reaches another. The other worker acts on the
    message with its own tools before it answers, so a tester can have the coder fix
    the bug it found.

    How the message travels is the injected send callable's business (the subagents
    layer hands it an A2A interaction), so the tool knows no agent and no transport. It
    caps the messages per step, because every answer costs the other worker a run."""

    def __init__(self, send: Callable[[str], str], peer_name: str, max_messages: int = 2) -> None:
        super().__init__()
        self._send: Callable[[str], str] = send
        self._peer_name: str = peer_name
        self._max_messages: int = max_messages
        self._delivered: int = 0

    @property
    def name(self) -> str:
        return "message_worker"

    @property
    def description(self) -> str:
        return (
            f"Send a message to the {self._peer_name} worker that wrote the code in this "
            f"workspace and get its answer. It can change the code before it answers, so use "
            f"it to have a problem you found fixed: say which file and function, the input, "
            f"and the expected and the actual result."
        )

    @property
    def input_schema(self) -> type[ToolMessageWorkerInput]:
        return ToolMessageWorkerInput

    @property
    def peer_name(self) -> str:
        return self._peer_name

    @property
    def max_messages(self) -> int:
        return self._max_messages

    @property
    def delivered(self) -> int:
        return self._delivered

    def execute(self, input: ToolMessageWorkerInput) -> str:
        if self._delivered >= self._max_messages:
            return (
                f"You have already sent the {self._peer_name} worker {self._delivered} "
                f"message(s), the most one step may send. Check what it changed with your "
                f"own tools and write your report."
            )

        answer = self._send(input.message)
        self._delivered += 1
        return (
            f"The {self._peer_name} worker answered:\n{answer}\n\n"
            f"Check what it says it changed with your own tools before you rely on it."
        )
