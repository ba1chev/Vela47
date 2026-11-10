from typing import Optional

from app.intelligence.agents import AgentBase
from app.intelligence.messages import MessageAI
from app.intelligence.tools import ToolRegistry
from app.intelligence.agents import PromptManager
from app.intelligence.messages import MessageHuman
from app.intelligence.memory import VectorDbMemory
from app.intelligence.model import ModelFoundation
from app.intelligence.agents import OperationContext
from app.intelligence.agents import OperationPipeline
from app.intelligence.tracing import TracingServiceBase


class DeepAgent(AgentBase):
    """The orchestrating agent. It never calls a model itself: every inference happens
    inside a pipeline layer, so the whole strategy is swapped by passing another
    OperationPolicy.

    What it owns is the conversation. Its memory accumulates the turns while each
    subagent starts from nothing: continuity at the top, isolation at the bottom.
    Earlier turns reach planning and merging as context.history, bounded by AgentBase. A
    run with no merged answer yields an empty MessageAI rather than raising, so the turn
    is still recorded."""

    def __init__(self, model: ModelFoundation, prompt_manager: PromptManager,
        max_context_window_size: int, operation_pipeline: OperationPipeline,
        tool_registry: Optional[ToolRegistry] = None,
        vector_db_memory: Optional[VectorDbMemory] = None,
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        super().__init__(
            model = model,
            prompt_manager = prompt_manager,
            max_context_window_size = max_context_window_size,
            tracing_service = tracing_service,
            tool_registry = tool_registry,
            vector_db_memory = vector_db_memory
        )
        self._operation_pipeline: OperationPipeline = operation_pipeline

    def execute(self, human_message: MessageHuman) -> MessageAI:
        history = self._history()
        self._append_human(human_message)
        context = self._operation_pipeline.run(
            OperationContext(goal = human_message, history = history)
        )
        response = context.final if context.final is not None else MessageAI(content = "")
        self._append_ai(response)
        return response
