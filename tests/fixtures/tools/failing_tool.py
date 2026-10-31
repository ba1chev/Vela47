from app.intelligence.tools import ToolBase
from tests.fixtures.tools.add_input import AddInput


class FailingTool(ToolBase[AddInput, int]):
    """Always raises. Exists so a test can prove the executor turns a tool's
    exception into an error MessageTool rather than letting it escape."""

    @property
    def name(self) -> str:
        return "fail"

    @property
    def description(self) -> str:
        return "Always raises."

    @property
    def input_schema(self) -> type[AddInput]:
        return AddInput

    def execute(self, input: AddInput) -> int:
        raise RuntimeError("tool exploded")
