from typing import Optional

from app.intelligence.tools import ToolRegistry
from app.intelligence.messages import MessageTool
from app.intelligence.tracing import TraceEventType
from app.intelligence.messages import MessageToolCall
from app.intelligence.security import SecurityMonitor
from app.intelligence.tracing import TracingServiceNull
from app.intelligence.tracing import TracingServiceBase


class ToolExecutor:
    """Bridges a MessageToolCall produced by the model with the concrete ToolBase
    instance that handles it: it resolves the tool by name, validates the arguments
    against the tool's input model, so bad arguments never reach execution, runs it and
    wraps the result in a MessageTool for the next turn. An exception becomes a
    MessageTool with status="error", so the model can decide how to recover.

    A result whose tool names a result_threat is inspected for it by a SecurityMonitor
    that reports to the same tracer. Every tool result passes here, so this is the one
    place that sees what a page or a document said before a model reads it; the result
    is passed on unchanged."""

    def __init__(self, registry: ToolRegistry,
        tracing_service: Optional[TracingServiceBase] = None,
        security_monitor: Optional[SecurityMonitor] = None) -> None:
        self._registry = registry
        self._tracing_service: TracingServiceBase = (
            tracing_service
            if tracing_service is not None
            else TracingServiceNull()
        )
        self._security_monitor: SecurityMonitor = (
            security_monitor
            if security_monitor is not None
            else SecurityMonitor(self._tracing_service)
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
                name = tool_call.name,
                content = f"Unknown tool '{tool_call.name}'.",
                status = "error"
            ))

        try:
            parsed_input = tool.input_schema.model_validate(tool_call.args)
            result = tool.execute(parsed_input)
            message = self._report(tool_call, MessageTool(
                tool_call_id = tool_call.id or "",
                name = tool_call.name,
                content = str(result),
                artifact = result,
                status = "success"
            ))
        except Exception as e:
            return self._report(tool_call, MessageTool(
                tool_call_id = tool_call.id or "",
                name = tool_call.name,
                content = str(e),
                status = "error"
            ))

        if tool.result_threat is not None:
            self._security_monitor.inspect(tool.result_threat, message.content, tool.name)
        return message
