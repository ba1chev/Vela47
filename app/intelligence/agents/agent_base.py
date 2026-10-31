from typing import Optional
from abc import ABC, abstractmethod

from app.intelligence.messages.message_ai import MessageAI
from app.intelligence.tools.tool_registry import ToolRegistry
from app.intelligence.tools.tool_executor import ToolExecutor
from app.intelligence.messages.message_tool import MessageTool
from app.intelligence.messages.message_type import MessageType
from app.intelligence.messages.message_human import MessageHuman
from app.intelligence.tracing.tracing_service import NullTracingService
from app.intelligence.agents.prompts.prompt_manager import PromptManager
from app.intelligence.messages.message_base.message_base import MessageBase
from app.intelligence.tracing.tracing_service_base import TracingServiceBase
from app.intelligence.memory.vector_db_memory.vector_db_memory import VectorDbMemory
from app.intelligence.model.model_foundation.model_foundation import ModelFoundation
from app.intelligence.memory.short_term_memory.short_term_memory import ShortTermMemory
from app.intelligence.memory.short_term_memory.context_window.context_window import ContextWindow


class AgentBase(ABC):
    """Abstract base for all agents in the system. Owns its ShortTermMemory and
    wires it to a ContextWindow. The context window policy is not set here —
    middleware injects it into the ContextWindow before each inference call.
    Concrete subclasses implement execute() and define the inference loop — how
    human messages turn into AI responses, whether tools are invoked, and how the
    context window is updated between turns. The vector_db_memory and tool_registry
    are optional: agents that do not need long-term retrieval or tool use omit them."""

    def __init__(self, model: ModelFoundation, prompt_manager: PromptManager,
        max_context_window_size: int, tool_registry: Optional[ToolRegistry] = None,
        vector_db_memory: Optional[VectorDbMemory] = None,
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        self._model: ModelFoundation = model
        self._prompt_manager: PromptManager = prompt_manager
        self._short_term_memory: ShortTermMemory = ShortTermMemory()
        self._context_window: ContextWindow = ContextWindow(
            memory = self._short_term_memory,
            max_window_size = max_context_window_size
        )
        self._tracing_service: TracingServiceBase = (
            tracing_service
            if tracing_service is not None
            else NullTracingService()
        )
        self._tool_registry: Optional[ToolRegistry] = tool_registry
        self._tool_executor: Optional[ToolExecutor] = (
            ToolExecutor(tool_registry, self._tracing_service)
            if tool_registry is not None else None
        )
        self._vector_db_memory: Optional[VectorDbMemory] = vector_db_memory

    def _append_human(self, message: MessageHuman) -> None:
        self._short_term_memory.append_message(message.content, MessageType.HUMAN_MESSAGE)

    def _append_ai(self, message: MessageAI) -> None:
        self._short_term_memory.append_message(message.content, MessageType.AI_MESSAGE)

    def _append_tool(self, message: MessageTool) -> None:
        self._short_term_memory.append_message(
            message.content,
            MessageType.TOOL_MESSAGE,
            tool_call_id = message.tool_call_id,
            status = message.status
        )

    def _compose_messages(self) -> list[MessageBase]:
        system_messages = self._prompt_manager.build_system_messages()
        return system_messages + self._context_window.build()

    def _build_messages(self) -> list[MessageBase]:
        self._context_window.update()
        return self._compose_messages()

    @abstractmethod
    def execute(self, human_message: MessageHuman) -> MessageAI:
        raise NotImplementedError("Must be implemented")
