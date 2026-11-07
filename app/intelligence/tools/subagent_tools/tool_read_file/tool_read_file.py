from app.intelligence.tools import ToolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.tools import ToolReadFileInput


class ToolReadFile(ToolBase[ToolReadFileInput, str]):
    """Returns a file's contents with line numbers, a window of lines at a time.

    A miss answers with the files that do exist instead of only reporting failure, so a
    wrong guess becomes a correctable one on the next turn instead of a dead end.

    Line numbers are added because the agent's job is usually to point at something: a
    review that can cite a line is worth more than one that paraphrases, and an edit is
    easier to aim at a line it has seen.

    A long file is returned MAX_LINES at a time, with the total and the line to continue
    from — the paging MCP's filesystem server offers as head and tail. One unbounded read
    of a large file would push the task itself out of a small model's context window."""

    MAX_LINES = 250
    MAX_LISTED_FILES = 40

    def __init__(self, sandbox_env: SandboxEnv) -> None:
        super().__init__()
        self._sandbox_env: SandboxEnv = sandbox_env

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "Read a file from your workspace and get it back with line numbers. Use it "
            "before judging, describing or editing any file, so you work from what is "
            "actually there rather than from memory. Long files come back in parts; the "
            "result says which line to continue from."
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

        total = len(lines)
        if input.start_line > total:
            return f"{input.path} has {total} lines, so there is nothing from line {input.start_line} on."
        if input.end_line is not None and input.end_line < input.start_line:
            return f"end_line {input.end_line} comes before start_line {input.start_line}."

        last = min(total, input.end_line or total, input.start_line + self.MAX_LINES - 1)
        width = len(str(last))
        numbered = "\n".join(
            f"{str(index).rjust(width)}  {lines[index - 1]}"
            for index in range(input.start_line, last + 1)
        )

        if input.start_line == 1 and last == total:
            return f"{input.path} ({total} lines):\n{numbered}"

        header = f"{input.path} (lines {input.start_line}-{last} of {total}):\n{numbered}"
        if last < total and (input.end_line is None or input.end_line > last):
            return header + (
                f"\n… {total - last} more lines. Call read_file with start_line={last + 1} "
                f"to continue."
            )
        return header

    def _miss(self, path: str) -> str:
        available = self._sandbox_env.list_files()

        if not available:
            return f"'{path}' does not exist, and the workspace is empty."

        listed = "\n".join(f"  {current}" for current in available[:self.MAX_LISTED_FILES])
        return f"'{path}' does not exist. The workspace contains:\n{listed}"
