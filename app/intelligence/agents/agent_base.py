from typing import Optional
from abc import ABC, abstractmethod

from app.intelligence.messages import MessageAI
from app.intelligence.tools import ToolRegistry
from app.intelligence.tools import ToolExecutor
from app.intelligence.messages import MessageTool
from app.intelligence.messages import MessageType
from app.intelligence.agents import PromptManager
from app.intelligence.messages import MessageBase
from app.intelligence.memory import ContextWindow
from app.intelligence.messages import MessageHuman
from app.intelligence.memory import VectorDbMemory
from app.intelligence.model import ModelFoundation
from app.intelligence.memory import ShortTermMemory
from app.intelligence.tracing import TracingServiceNull
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.memory import ContextWindowOperationShrink
from app.intelligence.memory import ContextWindowOperationTruncate


class AgentBase(ABC):
    """Abstract base for all agents. Owns a ShortTermMemory wired to a ContextWindow,
    whose policy middleware injects before each inference; subclasses implement
    execute(), the loop that turns a human message into a reply. vector_db_memory and
    tool_registry are optional.

    _history() is the bounded view of earlier turns an agent hands on: the last
    max_context_window_size messages, each cut to HISTORY_MESSAGE_CHARS, so a small
    model's context still fits the agent's own prompts. restore() refills the memory
    from a stored conversation, which is how an agent built for one request resumes a
    chat."""

    HISTORY_MESSAGE_CHARS = 1200

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
            else TracingServiceNull()
        )
        self._tool_registry: Optional[ToolRegistry] = tool_registry
        self._tool_executor: Optional[ToolExecutor] = (
            ToolExecutor(tool_registry, self._tracing_service)
            if tool_registry is not None else None
        )
        self._vector_db_memory: Optional[VectorDbMemory] = vector_db_memory
        self._history_shrink: ContextWindowOperationShrink = ContextWindowOperationShrink(
            n = max_context_window_size
        )
        self._history_truncate: ContextWindowOperationTruncate = ContextWindowOperationTruncate(
            max_chars = self.HISTORY_MESSAGE_CHARS
        )

    def _append_human(self, message: MessageHuman) -> None:
        self._short_term_memory.append_message(message.content, MessageType.HUMAN_MESSAGE)

    def _append_ai(self, message: MessageAI) -> None:
        self._short_term_memory.append_message(
            message.content,
            MessageType.AI_MESSAGE,
            tool_calls = message.tool_calls
        )

    def _append_tool(self, message: MessageTool) -> None:
        self._short_term_memory.append_message(
            message.content,
            MessageType.TOOL_MESSAGE,
            tool_call_id = message.tool_call_id,
            status = message.status,
            name = message.name
        )

    def _history(self) -> list[MessageBase]:
        return self._history_truncate.apply(
            self._history_shrink.apply(self._short_term_memory.get_all())
        )

    def restore(self, messages: list[MessageBase]) -> None:
        for current_message in messages:
            self._short_term_memory.append_message(current_message.content, current_message.type)

    def _compose_messages(self) -> list[MessageBase]:
        system_messages = self._prompt_manager.build_system_messages()
        return system_messages + self._context_window.build()

    def _build_messages(self) -> list[MessageBase]:
        self._context_window.update()
        return self._compose_messages()

    @abstractmethod
    def execute(self, human_message: MessageHuman) -> MessageAI:
        raise NotImplementedError("Must be implemented")
