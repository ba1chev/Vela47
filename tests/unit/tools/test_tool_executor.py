from pydantic import BaseModel

from app.tools.tool_base import ToolBase
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_executor import ToolExecutor
from app.messages.message_tool import MessageTool
from app.messages.message_tool_calls.message_tool_call import MessageToolCall


class AddInput(BaseModel):
    a: int
    b: int


class MultiplyInput(BaseModel):
    x: float
    y: float


class AddTool(ToolBase[AddInput, int]):
    @property
    def name(self): return "add"
    @property
    def description(self): return "Adds two integers."
    @property
    def input_schema(self): return AddInput
    def execute(self, input: AddInput) -> int:
        return self._function_predicate(input.a, input.b)


class MultiplyTool(ToolBase[MultiplyInput, float]):
    @property
    def name(self): return "multiply"
    @property
    def description(self): return "Multiplies two numbers."
    @property
    def input_schema(self): return MultiplyInput
    def execute(self, input: MultiplyInput) -> float:
        return self._function_predicate(input.x, input.y)


class FailingTool(ToolBase[AddInput, int]):
    @property
    def name(self): return "fail"
    @property
    def description(self): return "Always fails."
    @property
    def input_schema(self): return AddInput
    def execute(self, input: AddInput) -> int:
        raise RuntimeError("tool exploded")


def make_registry(*tools):
    reg = ToolRegistry()
    for t in tools:
        reg.register(t)
    return reg


class TestToolExecutor:
    def setup_method(self):
        self.registry = make_registry(
            AddTool(lambda a, b: a + b),
            MultiplyTool(lambda x, y: x * y),
            FailingTool(lambda a, b: a + b),
        )
        self.executor = ToolExecutor(self.registry)

    def _call(self, name, args, id = "c1"):
        return MessageToolCall(name = name, args = args, id = id)

    def test_successful_execution(self):
        result = self.executor.execute(self._call("add", {"a": 3, "b": 7}))
        assert isinstance(result, MessageTool)
        assert result.status == "success"
        assert result.content == "10"
        assert result.artifact == 10

    def test_tool_call_id_preserved(self):
        result = self.executor.execute(self._call("add", {"a": 1, "b": 1}, id = "xyz"))
        assert result.tool_call_id == "xyz"

    def test_unknown_tool_returns_error(self):
        result = self.executor.execute(self._call("unknown", {}))
        assert result.status == "error"
        assert "unknown" in result.content.lower() or "Unknown" in result.content

    def test_failing_tool_returns_error(self):
        result = self.executor.execute(self._call("fail", {"a": 1, "b": 2}))
        assert result.status == "error"
        assert "exploded" in result.content

    def test_invalid_args_returns_error(self):
        result = self.executor.execute(self._call("add", {"a": "not_int", "b": 2}))
        assert result.status == "error"

    def test_multiply_tool(self):
        result = self.executor.execute(self._call("multiply", {"x": 3.0, "y": 4.0}))
        assert result.status == "success"
        assert result.artifact == 12.0

    def test_missing_required_arg_returns_error(self):
        result = self.executor.execute(self._call("add", {"a": 5}))
        assert result.status == "error"

    def test_none_tool_call_id_uses_empty_string(self):
        call = MessageToolCall(name = "add", args = {"a": 1, "b": 2}, id = None)
        result = self.executor.execute(call)
        assert result.tool_call_id == ""
