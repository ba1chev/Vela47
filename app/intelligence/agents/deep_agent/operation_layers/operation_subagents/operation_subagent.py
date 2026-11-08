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
    would throw them away.

    A reply that calls no tool before any tool has been used is not taken as the answer.
    Small models often open by announcing what they are about to do — 'I will first
    search the user's documents…' — and stop there, and accepted as the result that
    announcement would reach the merging layer as if it were a finding. Such a reply is
    answered once with SUBAGENT_ACT_PROMPT and the loop goes on; a second one is
    accepted, because some tasks genuinely need no tool.

    The last turn is announced with SUBAGENT_REPORT_PROMPT. Given no tools and no word
    that they are gone, a model mid-task writes its next call out as text, and a raw
    <tool_call> block became the step's report — which the merging layer then turned
    into test results nobody ran. Any tool call written as text is removed from the
    report; if nothing is left, the report says the step ran out of turns and passes
    on the last tool result, which is real, instead of nothing.

    Around the loop run the probes of its type: before() as the task starts, after() once
    the report is written, with every message of the run. What they find is kept as
    evidence, beside the report rather than inside it, so the merging layer can tell the
    model's account of the step from what the system checked."""

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
