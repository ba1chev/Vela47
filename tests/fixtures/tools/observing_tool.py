from app.intelligence.messages import MessageBase
from tests.fixtures.tools.add_tool import AddTool


class ObservingTool(AddTool):
    """An AddTool that keeps every message it is shown through observe(), so a test can
    check which parts of an agent's conversation reach its tools."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.observed: list[MessageBase] = []

    def observe(self, message: MessageBase) -> None:
        self.observed.append(message)
