from pydantic import BaseModel

from app.tools.tool_base import ToolBase
from app.tools.tool_registry import ToolRegistry


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


def make_registry(*tools):
    reg = ToolRegistry()
    for t in tools:
        reg.register(t)
    return reg


class TestToolRegistry:
    def test_register_and_get(self):
        reg = make_registry(AddTool(lambda a, b: a + b))
        tool = reg.get("add")
        assert tool is not None
        assert tool.name == "add"

    def test_get_unknown_returns_none(self):
        reg = ToolRegistry()
        assert reg.get("unknown") is None

    def test_len(self):
        reg = make_registry(
            AddTool(lambda a, b: a + b),
            MultiplyTool(lambda x, y: x * y),
        )
        assert len(reg) == 2

    def test_contains(self):
        reg = make_registry(AddTool(lambda a, b: a + b))
        assert "add" in reg
        assert "multiply" not in reg

    def test_all_returns_list(self):
        reg = make_registry(AddTool(lambda a, b: a + b), MultiplyTool(lambda x, y: x * y))
        assert len(reg.all()) == 2

    def test_schemas_structure(self):
        reg = make_registry(AddTool(lambda a, b: a + b))
        schemas = reg.schemas()
        assert len(schemas) == 1
        schema = schemas[0]
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "add"
        assert "parameters" in schema["function"]

    def test_schemas_contain_input_properties(self):
        reg = make_registry(AddTool(lambda a, b: a + b))
        params = reg.schemas()[0]["function"]["parameters"]
        assert "a" in params["properties"]
        assert "b" in params["properties"]

    def test_register_overwrites_same_name(self):
        reg = ToolRegistry()
        reg.register(AddTool(lambda a, b: a + b))
        reg.register(AddTool(lambda a, b: a - b))
        assert len(reg) == 1
