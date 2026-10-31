from app.intelligence.tools.tool_base import ToolBase
from app.intelligence.middleware.middleware_base import MiddlewareBase
from app.intelligence.agents.prompts.prompt_manager import PromptManager
from app.intelligence.model.model_foundation.model_foundation import ModelFoundation
from app.intelligence.memory.short_term_memory.context_window.context_window import ContextWindow


class OperationSubagentBlueprint:
    """The full recipe for one kind of subagent — which tool it gets, which model
    it runs on, how its context window is managed, and how long its ReAct loop may
    run. Holds only stateless collaborators, which is what makes it reusable: the
    factory builds a fresh OperationSubagent from the same blueprint for every
    task, and each gets its own ShortTermMemory and ContextWindow while sharing
    the model and tool instances.

    Keeping the recipe in a blueprint rather than hard-coding it in the factory is
    what lets a RESEARCH agent run a small fast model with a sliding window while
    a REVIEW agent runs a reasoning model with summarisation, without either being
    a separate class."""

    def __init__(self, tool: ToolBase, model: ModelFoundation,
        prompt_manager: PromptManager, max_context_window_size: int,
        context_window_middleware: MiddlewareBase[ContextWindow],
        max_iterations: int = 5) -> None:
        self.tool: ToolBase = tool
        self.model: ModelFoundation = model
        self.prompt_manager: PromptManager = prompt_manager
        self.max_context_window_size: int = max_context_window_size
        self.context_window_middleware: MiddlewareBase[ContextWindow] = context_window_middleware
        self.max_iterations: int = max_iterations
