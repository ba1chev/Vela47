from app.intelligence.tools import ToolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.tools import ToolReadFileInput


class ToolReadFile(ToolBase[ToolReadFileInput, str]):
    """Returns a file's contents with line numbers.

    A miss answers with the files that do exist instead of only reporting failure.
    The agent cannot list the workspace separately — it has this tool and nothing
    else — so a bare 'not found' would be a dead end, while the listing turns a
    wrong guess into a correctable one on the next turn.

    Line numbers are added because the agent's job is usually to point at something:
    a review that can cite a line is worth more than one that paraphrases."""

    def __init__(self, sandbox_env: SandboxEnv) -> None:
        super().__init__()
        self._sandbox_env: SandboxEnv = sandbox_env

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "Read a file from your workspace and get it back with line numbers. "
            "Use it before judging or describing any file, so you work from what is "
            "actually there rather than from memory."
        )

    @property
    def input_schema(self) -> type[ToolReadFileInput]:
        return ToolReadFileInput

    def execute(self, input: ToolReadFileInput) -> str:
        try:
            content = self._sandbox_env.read_file(input.path)
        except FileNotFoundError:
            return self._miss(input.path)

        lines = content.splitlines()
        if not lines:
            return f"{input.path} exists but is empty."

        width = len(str(len(lines)))
        numbered = "\n".join(
            f"{str(index).rjust(width)}  {current_line}"
            for index, current_line in enumerate(lines, start = 1)
        )
        return f"{input.path} ({len(lines)} lines):\n{numbered}"

    def _miss(self, path: str) -> str:
        available = self._sandbox_env.list_files()

        if not available:
            return f"'{path}' does not exist, and the workspace is empty."

        listed = "\n".join(f"  {current}" for current in available[:40])
        return f"'{path}' does not exist. The workspace contains:\n{listed}"
