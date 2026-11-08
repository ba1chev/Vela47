from typing import Callable, Optional

from app.intelligence.tools import ToolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.memory import ContextWindow
from app.intelligence.model import ModelFoundation
from app.intelligence.middleware import MiddlewareBase
from app.intelligence.agents import OperationSubagentProbeBase


class OperationSubagentBlueprint:
    """The full recipe for one kind of subagent — how to build its tools, which model
    it runs on, how its context window is managed, and how long its ReAct loop may run.

    The tools arrive as factories rather than instances because they cannot exist yet:
    a tool acts on the sandbox its agent was leased, and that lease is only made when
    a task is dispatched. One shared instance would have every subagent writing into
    whichever sandbox happened to be bound first. A tool that needs something besides
    the sandbox — the web, the user's documents — is a closure over it that ignores the
    sandbox it is handed.

    The prompt is a template for the same reason. It names the tools, which a small
    model needs in order to call them reliably, and the names are only knowable once the
    factories have produced the tools — so the text is finished at creation time, not
    here.

    Keeping the recipe in a blueprint rather than hard-coding it in the factory is
    what lets a RESEARCH agent run a small fast model with a sliding window while a
    REVIEW agent runs a reasoning model with summarisation, without either being a
    separate class.

    Probes arrive as factories for the same reason tools do: a probe checks the sandbox of
    one task. They are what the system verifies about a step after the subagent is done —
    the workspace it changed, the tests as they really run — and a type with none is
    reported on its own word alone."""

    def __init__(self, tool_factories: list[Callable[[SandboxEnv], ToolBase]],
        prompt_template: str, model: ModelFoundation, max_context_window_size: int,
        context_window_middleware: MiddlewareBase[ContextWindow],
        max_iterations: int = 6,
        probe_factories: Optional[list[Callable[[SandboxEnv], OperationSubagentProbeBase]]] = None) -> None:
        self.tool_factories: list[Callable[[SandboxEnv], ToolBase]] = list(tool_factories)
        self.probe_factories: list[Callable[[SandboxEnv], OperationSubagentProbeBase]] = list(probe_factories or [])
        self.prompt_template: str = prompt_template
        self.model: ModelFoundation = model
        self.max_context_window_size: int = max_context_window_size
        self.context_window_middleware: MiddlewareBase[ContextWindow] = context_window_middleware
        self.max_iterations: int = max_iterations
