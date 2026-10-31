from typing import Optional

from app.intelligence.tools.tool_base import ToolBase
from app.intelligence.agents.agent_base import AgentBase
from app.intelligence.messages.message_ai import MessageAI
from app.intelligence.tools.tool_registry import ToolRegistry
from app.intelligence.messages.message_human import MessageHuman
from app.intelligence.middleware.middleware_base import MiddlewareBase
from app.intelligence.agents.prompts.prompt_manager import PromptManager
from app.intelligence.tracing.tracing_service_base import TracingServiceBase
from app.intelligence.model.model_foundation.model_foundation import ModelFoundation
from app.intelligence.memory.short_term_memory.context_window.context_window import ContextWindow


class OperationSubagent(AgentBase):
    """A deliberately primitive ReAct agent that owns exactly one tool. One tool
    is the whole design: it removes tool selection from the model's job, so the
    only decision left each turn is whether to call it or answer, which is what
    makes these agents reliable enough to run unsupervised inside a pipeline.
    Anything needing two capabilities is two subagents and therefore two plan
    steps.

    Each instance keeps its own ShortTermMemory and ContextWindow inherited from
    AgentBase, and is handed its own model and context window middleware — so a
    cheap fast model with a sliding window and an expensive model with
    summarisation can run side by side in the same pipeline.

    The loop runs at most max_iterations times. Reaching the cap returns the last
    response rather than raising: a subagent that keeps calling its tool without
    concluding still has partial findings worth merging, and the caller sees the
    truncation through the result's status."""

    def __init__(self, model: ModelFoundation, prompt_manager: PromptManager,
        max_context_window_size: int, tool: ToolBase,
        context_window_middleware: MiddlewareBase[ContextWindow],
        max_iterations: int = 5,
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        tool_registry = ToolRegistry()
        tool_registry.register(tool)
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

        return response
