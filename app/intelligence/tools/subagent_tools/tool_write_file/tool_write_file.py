from app.intelligence.tools.tool_base import ToolBase
from app.intelligence.sandbox.sandbox_env.sandbox_env import SandboxEnv
from app.intelligence.tools.subagent_tools.tool_write_file.tool_write_file_input import ToolWriteFileInput


class ToolWriteFile(ToolBase[ToolWriteFileInput, str]):
    """Writes a file into the sandbox.

    Whole-file writes rather than patches: a small model asked to produce a diff
    against a file it cannot see reliably produces a diff that does not apply, and
    a failed patch is harder to recover from than a rewritten file.

    The file outlives the subagent that wrote it. Sandbox slots are leased per task
    but the directory belongs to the run, so what a CODE subagent writes here is
    what a REVIEW subagent later reads — the only channel through which two isolated
    subagents can collaborate."""

    def __init__(self, sandbox_env: SandboxEnv) -> None:
        super().__init__()
        self._sandbox_env: SandboxEnv = sandbox_env

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return (
            "Write a file into your workspace, creating or replacing it. Use it to "
            "deliver the implementation your task asks for — write the real code "
            "rather than describing what you would write."
        )

    @property
    def input_schema(self) -> type[ToolWriteFileInput]:
        return ToolWriteFileInput

    def execute(self, input: ToolWriteFileInput) -> str:
        written = self._sandbox_env.write_file(input.path, input.content)
        line_count = len(input.content.splitlines())
        return f"Wrote {written} ({line_count} lines)."
