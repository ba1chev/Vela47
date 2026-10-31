from pydantic import BaseModel

from app.intelligence.tools import ToolBase
from app.intelligence.tools import ToolRegistry
from tests.fixtures.tools.add_tool import AddTool
from tests.fixtures.tools.add_input import AddInput
from tests.fixtures.tools.multiply_tool import MultiplyTool
from tests.fixtures.tools.multiply_input import MultiplyInput


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
