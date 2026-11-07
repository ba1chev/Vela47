from typing import Optional

from app.intelligence.tools import ToolBase
from app.intelligence.agents import AgentBase
from app.intelligence.messages import MessageAI
from app.intelligence.tools import ToolRegistry
from app.intelligence.agents import PromptManager
from app.intelligence.memory import ContextWindow
from app.intelligence.messages import MessageHuman
from app.intelligence.model import ModelFoundation
from app.intelligence.middleware import MiddlewareBase
from app.intelligence.tracing import TracingServiceBase


class OperationSubagent(AgentBase):
    """A deliberately primitive ReAct agent that owns a small, fixed toolset. Small is
    the design: a type gets only the three or four tools its job needs — a CODE agent can
    look, read, write and edit; a TEST agent can look, read, write tests and run them —
    so choosing a tool stays a narrow decision a small model makes reliably, while the
    agent can still check its own work inside one step. Anything outside its toolset is
    another type and therefore another plan step.

    Each instance keeps its own ShortTermMemory and ContextWindow inherited from
    AgentBase, and is handed its own model and context window middleware — so a
    cheap fast model with a sliding window and an expensive model with
    summarisation can run side by side in the same pipeline.

    The loop runs at most max_iterations times. A model still calling tools when the cap
    is reached gets one last turn with the tools withdrawn, so it has to write up what
    its tool results show instead of ending on a call nobody will answer — a subagent
    that ran out of turns still has partial findings worth merging, and an empty reply
    would throw them away."""

    def __init__(self, model: ModelFoundation, prompt_manager: PromptManager,
        max_context_window_size: int, tools: list[ToolBase],
        context_window_middleware: MiddlewareBase[ContextWindow],
        max_iterations: int = 6,
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        tool_registry = ToolRegistry()
        for current_tool in tools:
            tool_registry.register(current_tool)
        super().__init__(
            model = model,
            prompt_manager = prompt_manager,
            max_context_window_size = max_context_window_size,
            tool_registry = tool_registry,
            tracing_service = tracing_service
        )
        self._context_window_middleware = context_window_middleware
        self._max_iterations = max_iterations

    def execute(self, human_message: MessageHuman) -> MessageAI:
        self._append_human(human_message)
        response = MessageAI(content = "")

        for _ in range(self._max_iterations):
            self._context_window_middleware.process(self._context_window)
            response = self._model.invoke(
                self._compose_messages(),
                tools = self._tool_registry.schemas()
            )
            self._append_ai(response)

            if not response.tool_calls:
                return response

            for current_call in response.tool_calls:
                self._append_tool(self._tool_executor.execute(current_call))

        self._context_window_middleware.process(self._context_window)
        response = self._model.invoke(self._compose_messages())
        self._append_ai(response)
        return response
