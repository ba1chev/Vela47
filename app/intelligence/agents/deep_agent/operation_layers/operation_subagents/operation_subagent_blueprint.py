from typing import Callable

from app.intelligence.tools import ToolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.memory import ContextWindow
from app.intelligence.model import ModelFoundation
from app.intelligence.middleware import MiddlewareBase


class OperationSubagentBlueprint:
    """The full recipe for one kind of subagent — how to build its tool, which model
    it runs on, how its context window is managed, and how long its ReAct loop may run.

    The tool arrives as a factory rather than an instance because it cannot exist yet:
    a tool acts on the sandbox its agent was leased, and that lease is only made when
    a task is dispatched. One shared instance would have every subagent writing into
    whichever sandbox happened to be bound first.

    The prompt is a template for the same reason. It has to name the tool for a small
    model to reliably call it, and the tool's name is only knowable once the factory
    has produced one — so the text is finished at creation time, not here.

    Keeping the recipe in a blueprint rather than hard-coding it in the factory is
    what lets a RESEARCH agent run a small fast model with a sliding window while a
    REVIEW agent runs a reasoning model with summarisation, without either being a
    separate class."""

    def __init__(self, tool_factory: Callable[[SandboxEnv], ToolBase],
        prompt_template: str, model: ModelFoundation, max_context_window_size: int,
        context_window_middleware: MiddlewareBase[ContextWindow],
        max_iterations: int = 5) -> None:
        self.tool_factory: Callable[[SandboxEnv], ToolBase] = tool_factory
        self.prompt_template: str = prompt_template
        self.model: ModelFoundation = model
        self.max_context_window_size: int = max_context_window_size
        self.context_window_middleware: MiddlewareBase[ContextWindow] = context_window_middleware
        self.max_iterations: int = max_iterations
