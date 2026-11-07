from typing import Optional

from app.intelligence.agents import AgentBase
from app.intelligence.agents import RagContext
from app.intelligence.messages import MessageAI
from app.intelligence.agents import RagPipeline
from app.intelligence.agents import PromptManager
from app.intelligence.messages import MessageHuman
from app.intelligence.memory import VectorDbMemory
from app.intelligence.model import ModelFoundation
from app.intelligence.tracing import TracingServiceBase


class RagAgent(AgentBase):
    """The agent that answers from the user's documents. It shares the DeepAgent's
    surface — execute() takes a question and returns an answer, restore() resumes a
    stored conversation, the history it passes on is bounded by AgentBase — so the
    server runs either one the same way and a conversation can move between them.

    Like the DeepAgent it never calls a model itself. Every inference happens inside a
    RagPipeline layer, and the strategy is whatever RagPolicy that pipeline was built
    from. The vector memory holding the documents is given to the pipeline's retrieval
    layer, and to this agent as well so that it is reachable from the agent like any
    other long-term memory.

    A run that produces no answer yields an empty MessageAI rather than raising, so the
    turn is still recorded and the caller still gets a message to inspect."""

    def __init__(self, model: ModelFoundation, prompt_manager: PromptManager,
        max_context_window_size: int, rag_pipeline: RagPipeline,
        vector_db_memory: Optional[VectorDbMemory] = None,
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        super().__init__(
            model = model,
            prompt_manager = prompt_manager,
            max_context_window_size = max_context_window_size,
            vector_db_memory = vector_db_memory,
            tracing_service = tracing_service
        )
        self._rag_pipeline: RagPipeline = rag_pipeline

    def execute(self, human_message: MessageHuman) -> MessageAI:
        history = self._history()
        self._append_human(human_message)
        context = self._rag_pipeline.run(RagContext(goal = human_message, history = history))
        response = context.final if context.final is not None else MessageAI(content = "")
        self._append_ai(response)
        return response
