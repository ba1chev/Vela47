from typing import Optional

from app.intelligence.tools.tool_registry import ToolRegistry
from app.intelligence.messages.message_tool import MessageTool
from app.intelligence.tracing.trace_event_type import TraceEventType
from app.intelligence.tracing.tracing_service_null import TracingServiceNull
from app.intelligence.tracing.tracing_service_base import TracingServiceBase
from app.intelligence.messages.message_tool_calls.message_tool_call import MessageToolCall


class ToolExecutor:
    """Bridges a MessageToolCall produced by the model with the concrete
    ToolBase instance that handles it. For each call it:
      1. Resolves the tool by name from the registry.
      2. Validates and parses MessageToolCall.args into the tool's TInput
         model via Pydantic model_validate — raising ValidationError on
         schema mismatch rather than letting bad args reach execution.
      3. Calls tool.execute(input) and captures the result.
      4. Wraps the result in a MessageTool so it can be appended to memory
         and returned to the model in the next turn.
    Execution errors are caught and surfaced as a MessageTool with
    status="error" so the model can decide how to recover."""

    def __init__(self, registry: ToolRegistry,
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        self._registry = registry
        self._tracing_service: TracingServiceBase = (
            tracing_service
            if tracing_service is not None
            else TracingServiceNull()
        )

    def _report(self, tool_call: MessageToolCall, result: MessageTool) -> MessageTool:
        self._tracing_service.emit(
            TraceEventType.TOOL_EXECUTED,
            tool_call.name,
            {
                "status": result.status,
                "args": tool_call.args,
                "result": result.content
                if isinstance(result.content, str)
                else str(result.content)
            }
        )
        return result

    def execute(self, tool_call: MessageToolCall) -> MessageTool:
        tool = self._registry.get(tool_call.name)

        if tool is None:
            return self._report(tool_call, MessageTool(
                tool_call_id = tool_call.id or "",
                content = f"Unknown tool '{tool_call.name}'.",
                status = "error"
            ))

        try:
            parsed_input = tool.input_schema.model_validate(tool_call.args)
            result = tool.execute(parsed_input)
            return self._report(tool_call, MessageTool(
                tool_call_id = tool_call.id or "",
                content = str(result),
                artifact = result,
                status = "success"
            ))
        except Exception as e:
            return self._report(tool_call, MessageTool(
                tool_call_id = tool_call.id or "",
                content = str(e),
                status = "error"
            ))
