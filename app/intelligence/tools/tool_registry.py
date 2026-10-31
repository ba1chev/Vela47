from app.intelligence.tools.tool_base import ToolBase


class ToolRegistry:
    """Central registry that maps tool names to their ToolBase instances.
    The agent populates the registry at startup and passes it to the
    ToolExecutor. The model receives the registered tools' schemas at
    inference time so it can choose which to invoke; the registry then
    resolves the chosen name back to the concrete instance for execution."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolBase] = {}

    def register(self, tool: ToolBase) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolBase | None:
        return self._tools.get(name)

    def all(self) -> list[ToolBase]:
        return list(self._tools.values())

    def schemas(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema.model_json_schema()
                }
            }
            for tool in self._tools.values()
        ]

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
