from app.intelligence.tools import ToolBase
from tests.fixtures.tools.multiply_input import MultiplyInput


class MultiplyTool(ToolBase[MultiplyInput, float]):
    """A second tool with a different name and schema, so registry and executor
    tests can tell one tool from another."""

    @property
    def name(self) -> str:
        return "multiply"

    @property
    def description(self) -> str:
        return "Multiplies two numbers."

    @property
    def input_schema(self) -> type[MultiplyInput]:
        return MultiplyInput

    def execute(self, input: MultiplyInput) -> float:
        return self._function_predicate(input.x, input.y)
