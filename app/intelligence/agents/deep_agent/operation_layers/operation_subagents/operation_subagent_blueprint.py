from typing import Callable, Optional

from app.intelligence.tools import ToolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.memory import ContextWindow
from app.intelligence.model import ModelFoundation
from app.intelligence.middleware import MiddlewareBase
from app.intelligence.agents import OperationSubagentProbeBase


class OperationSubagentBlueprint:
    """The recipe for one kind of subagent: its tool and probe factories, prompt
    template, model, context window management and iteration cap. Kept as data, so types
    can run different models or window policies without being separate classes.

    Tools and probes arrive as factories because they act on the sandbox of one task,
    which only exists once the task is dispatched; a tool that needs something else,
    such as the web, is a closure that ignores the sandbox. The prompt is a template for
    the same reason: it names the tools, and the names are only known once they are
    built."""

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
