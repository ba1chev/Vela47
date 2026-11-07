from typing import Optional

from app.intelligence.agents import AgentBase
from app.intelligence.messages import MessageAI
from app.intelligence.tools import ToolRegistry
from app.intelligence.messages import MessageBase
from app.intelligence.agents import PromptManager
from app.intelligence.messages import MessageHuman
from app.intelligence.memory import VectorDbMemory
from app.intelligence.model import ModelFoundation
from app.intelligence.agents import OperationContext
from app.intelligence.agents import OperationPipeline
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.memory import ContextWindowOperationShrink
from app.intelligence.memory import ContextWindowOperationTruncate


class DeepAgent(AgentBase):
    """The orchestrating agent. Unlike a subagent, it never calls a model itself —
    every inference happens inside a pipeline layer, which is what keeps the
    orchestration logic free of prompt handling and makes the whole strategy
    swappable by passing a different OperationPolicy.

    What it does own is the conversation. Each turn is recorded in its
    ShortTermMemory, so the DeepAgent accumulates a history across turns while
    each subagent it spawns starts from nothing. That asymmetry is the point:
    continuity lives at the top, isolation lives at the bottom.

    The earlier turns reach the pipeline as context.history, which is what lets
    planning resolve a follow-up and merging continue the conversation. They are
    bounded twice — the last max_context_window_size messages, each cut to
    HISTORY_MESSAGE_CHARS — because a small model's context also has to hold the
    planning schema, and a long conversation would quietly push it out. restore()
    refills the memory from a stored conversation, which is how a DeepAgent built
    for one request resumes a chat that began in an earlier one.

    A run that produces no merged answer — a policy configured without a merging
    stage, or a plan with no executable steps — yields an empty MessageAI rather
    than raising, so the turn is still recorded and the caller still gets a
    message to inspect."""

    HISTORY_MESSAGE_CHARS = 1200

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
        self._history_shrink: ContextWindowOperationShrink = ContextWindowOperationShrink(
            n = max_context_window_size
        )
        self._history_truncate: ContextWindowOperationTruncate = ContextWindowOperationTruncate(
            max_chars = self.HISTORY_MESSAGE_CHARS
        )

    def _history(self) -> list[MessageBase]:
        return self._history_truncate.apply(
            self._history_shrink.apply(self._short_term_memory.get_all())
        )

    def restore(self, messages: list[MessageBase]) -> None:
        for current_message in messages:
            self._short_term_memory.append_message(current_message.content, current_message.type)

    def execute(self, human_message: MessageHuman) -> MessageAI:
        history = self._history()
        self._append_human(human_message)
        context = self._operation_pipeline.run(
            OperationContext(goal = human_message, history = history)
        )
        response = context.final if context.final is not None else MessageAI(content = "")
        self._append_ai(response)
        return response
