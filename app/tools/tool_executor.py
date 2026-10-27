from app.tools.tool_registry import ToolRegistry
from app.messages.message_tool import MessageTool
from app.messages.message_tool_calls.message_tool_call import MessageToolCall


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

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def execute(self, tool_call: MessageToolCall) -> MessageTool:
        tool = self._registry.get(tool_call.name)

        if tool is None:
            return MessageTool(
                tool_call_id = tool_call.id or "",
                content = f"Unknown tool '{tool_call.name}'.",
                status = "error"
            )

        try:
            parsed_input = tool.input_schema.model_validate(tool_call.args)
            result = tool.execute(parsed_input)
            return MessageTool(
                tool_call_id = tool_call.id or "",
                content = str(result),
                artifact = result,
                status = "success"
            )
        except Exception as e:
            return MessageTool(
                tool_call_id = tool_call.id or "",
                content = str(e),
                status = "error"
            )
