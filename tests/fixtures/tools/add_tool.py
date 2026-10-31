from app.intelligence.tools import ToolBase
from tests.fixtures.tools.add_input import AddInput


class AddTool(ToolBase[AddInput, int]):
    """Adds two integers through an injected predicate, so a test can decide what
    "adding" means — including making it raise."""

    @property
    def name(self) -> str:
        return "add"

    @property
    def description(self) -> str:
        return "Adds two integers."

    @property
    def input_schema(self) -> type[AddInput]:
        return AddInput

    def execute(self, input: AddInput) -> int:
        return self._function_predicate(input.a, input.b)
