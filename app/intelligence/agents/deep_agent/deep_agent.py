from typing import Optional

from app.intelligence.agents.agent_base import AgentBase
from app.intelligence.messages.message_ai import MessageAI
from app.intelligence.tools.tool_registry import ToolRegistry
from app.intelligence.messages.message_human import MessageHuman
from app.intelligence.agents.prompts.prompt_manager import PromptManager
from app.intelligence.agents.deep_agent.operation_context import OperationContext
from app.intelligence.agents.deep_agent.operation_pipeline import OperationPipeline
from app.intelligence.memory.vector_db_memory.vector_db_memory import VectorDbMemory
from app.intelligence.model.model_foundation.model_foundation import ModelFoundation


class DeepAgent(AgentBase):
    """The orchestrating agent. Unlike a subagent, it never calls a model itself —
    every inference happens inside a pipeline layer, which is what keeps the
    orchestration logic free of prompt handling and makes the whole strategy
    swappable by passing a different OperationPolicy.

    What it does own is the conversation. Each turn is recorded in its
    ShortTermMemory, so the DeepAgent accumulates a history across turns while
    each subagent it spawns starts from nothing. That asymmetry is the point:
    continuity lives at the top, isolation lives at the bottom.

    A run that produces no merged answer — a policy configured without a merging
    stage, or a plan with no executable steps — yields an empty MessageAI rather
    than raising, so the turn is still recorded and the caller still gets a
    message to inspect."""

    def __init__(self, model: ModelFoundation, prompt_manager: PromptManager,
        max_context_window_size: int, operation_pipeline: OperationPipeline,
        tool_registry: Optional[ToolRegistry] = None,
        vector_db_memory: Optional[VectorDbMemory] = None) -> None:
        super().__init__(
            model = model,
            prompt_manager = prompt_manager,
            max_context_window_size = max_context_window_size,
            tool_registry = tool_registry,
            vector_db_memory = vector_db_memory
        )
        self._operation_pipeline: OperationPipeline = operation_pipeline

    def execute(self, human_message: MessageHuman) -> MessageAI:
        self._append_human(human_message)
        context = self._operation_pipeline.run(OperationContext(goal = human_message))
        response = context.final if context.final is not None else MessageAI(content = "")
        self._append_ai(response)
        return response
