import re
from typing import Optional

from app.intelligence.tools import ToolBase
from app.intelligence.agents import AgentBase
from app.intelligence.messages import MessageAI
from app.intelligence.tools import ToolRegistry
from app.intelligence.agents import PromptManager
from app.intelligence.memory import ContextWindow
from app.intelligence.messages import MessageTool
from app.intelligence.messages import MessageHuman
from app.intelligence.model import ModelFoundation
from app.intelligence.middleware import MiddlewareBase
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.agents import SUBAGENT_ACT_PROMPT
from app.intelligence.agents import SUBAGENT_REPORT_PROMPT
from app.intelligence.agents import OperationSubagentProbeBase


class OperationSubagent(AgentBase):
    """A deliberately primitive ReAct agent over a small fixed toolset: three or four
    tools per type, so picking one stays a narrow decision a small model makes reliably.

    The loop runs at most max_iterations turns, then one last turn with the tools
    withdrawn and announced through SUBAGENT_REPORT_PROMPT, so the model writes up its
    results instead of a call nobody will answer. A first reply that calls no tool is
    answered once with SUBAGENT_ACT_PROMPT, since small models open by announcing what
    they will do. Tool calls written as text are stripped from the report; if nothing is
    left, the last real tool result is passed on. The probes of its type run around the
    loop, and what they find is kept as evidence beside the report."""

    TOOL_CALL_TEXT = re.compile(r"<tool_call>.*?(</tool_call>|$)", re.DOTALL)
    LAST_RESULT_CHARS = 1200

    def __init__(self, model: ModelFoundation, prompt_manager: PromptManager,
        max_context_window_size: int, tools: list[ToolBase],
        context_window_middleware: MiddlewareBase[ContextWindow],
        max_iterations: int = 6,
        tracing_service: Optional[TracingServiceBase] = None,
        probes: Optional[list[OperationSubagentProbeBase]] = None) -> None:
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
        self._probes: list[OperationSubagentProbeBase] = list(probes or [])
        self._evidence: list[str] = []

    @property
    def evidence(self) -> list[str]:
        return list(self._evidence)

    def execute(self, human_message: MessageHuman) -> MessageAI:
        for current_probe in self._probes:
            current_probe.before()
        response = self._react(human_message)
        messages = self._short_term_memory.get_all()
        self._evidence = [
            current_fact for current_probe in self._probes for current_fact in current_probe.after(messages)
        ]
        return response

    def _react(self, human_message: MessageHuman) -> MessageAI:
        self._append_human(human_message)
        response = MessageAI(content = "")
        used_tools = False
        reminded = False

        for _ in range(self._max_iterations):
            self._context_window_middleware.process(self._context_window)
            response = self._model.invoke(
                self._compose_messages(),
                tools = self._tool_registry.schemas()
            )
            self._append_ai(response)

            if not response.tool_calls:
                if used_tools or reminded:
                    return self._report(response)
                reminded = True
                self._append_human(MessageHuman(content = SUBAGENT_ACT_PROMPT))
                continue

            used_tools = True
            for current_call in response.tool_calls:
                self._append_tool(self._tool_executor.execute(current_call))

        self._append_human(MessageHuman(content = SUBAGENT_REPORT_PROMPT))
        self._context_window_middleware.process(self._context_window)
        response = self._model.invoke(self._compose_messages())
        self._append_ai(response)
        return self._report(response)

    def _report(self, response: MessageAI) -> MessageAI:
        content = response.content if isinstance(response.content, str) else str(response.content)
        cleaned = self.TOOL_CALL_TEXT.sub("", content).strip()
        if cleaned == content.strip():
            return response
        if cleaned:
            return MessageAI(content = cleaned)

        last = next(
            (current for current in reversed(self._short_term_memory.get_all()) if isinstance(current, MessageTool)),
            None
        )
        if last is None:
            return MessageAI(content = "This step ran out of turns before it did anything.")
        result = last.content if isinstance(last.content, str) else str(last.content)
        return MessageAI(content = (
            f"This step ran out of turns before writing its report. Its last tool result, from "
            f"{last.name}, was:\n{result[:self.LAST_RESULT_CHARS]}"
        ))
