from typing import Optional
from abc import ABC, abstractmethod

from app.messages.message_ai import MessageAI
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_executor import ToolExecutor
from app.messages.message_type import MessageType
from app.messages.message_human import MessageHuman
from app.agents.prompts.prompt_manager import PromptManager
from app.memory.vector_db_memory.vector_db_memory import VectorDbMemory
from app.model.model_foundation.model_foundation import ModelFoundation
from app.memory.short_term_memory.short_term_memory import ShortTermMemory
from app.memory.short_term_memory.context_window.context_window import ContextWindow


class Agent(ABC):
    """Abstract base for all agents in the system. Owns its ShortTermMemory and
    wires it to a ContextWindow. The context window policy is not set here —
    middleware injects it into the ContextWindow before each inference call.
    Concrete subclasses implement execute() and define the inference loop — how
    human messages turn into AI responses, whether tools are invoked, and how the
    context window is updated between turns. The vector_db_memory and tool_registry
    are optional: agents that do not need long-term retrieval or tool use omit them."""

    def __init__(self, model: ModelFoundation, prompt_manager: PromptManager,
        max_context_window_size: int, tool_registry: Optional[ToolRegistry] = None,
        vector_db_memory: Optional[VectorDbMemory] = None) -> None:
        self._model: ModelFoundation = model
        self._prompt_manager: PromptManager = prompt_manager
        self._short_term_memory: ShortTermMemory = ShortTermMemory()
        self._context_window: ContextWindow = ContextWindow(
            memory = self._short_term_memory,
            max_window_size = max_context_window_size
        )
        self._tool_registry: Optional[ToolRegistry] = tool_registry
        self._tool_executor: Optional[ToolExecutor] = (
            ToolExecutor(tool_registry) if tool_registry is not None else None
        )
        self._vector_db_memory: Optional[VectorDbMemory] = vector_db_memory

    def _append_human(self, message: MessageHuman) -> None:
        self._short_term_memory.append_message(message.content, MessageType.HUMAN_MESSAGE)

    def _append_ai(self, message: MessageAI) -> None:
        self._short_term_memory.append_message(message.content, MessageType.AI_MESSAGE)

    def _build_messages(self) -> list:
        self._context_window.update()
        system_messages = self._prompt_manager.build_system_messages()
        return system_messages + self._context_window.build()

    @abstractmethod
    def execute(self, human_message: MessageHuman) -> MessageAI:
        raise NotImplementedError("Must be implemented")
