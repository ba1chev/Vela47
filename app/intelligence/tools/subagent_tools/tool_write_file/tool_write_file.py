from typing import Optional

from app.intelligence.tools import ToolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.tools import ToolWriteFileInput
from app.intelligence.tools import python_syntax_warning


class ToolWriteFile(ToolBase[ToolWriteFileInput, str]):
    """Writes a whole file into the sandbox, creating or replacing it, and says which:
    replacing a file the agent did not know existed is the mistake worth noticing. A
    Python file that does not parse is reported on the spot. Changing part of a file is
    edit_file's job, since a small model rewriting a whole file tends to drop something.

    The file outlives the subagent. The directory belongs to the run, so what a CODE
    subagent writes is what a TEST or REVIEW subagent reads later."""

    def __init__(self, sandbox_env: SandboxEnv) -> None:
        super().__init__()
        self._sandbox_env: SandboxEnv = sandbox_env

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return (
            "Write a whole file into your workspace, creating it or replacing it. Use it "
            "to deliver a new file — write the real, complete code rather than describing "
            "it. To change part of a file that already exists, use edit_file instead."
        )

    @property
    def input_schema(self) -> type[ToolWriteFileInput]:
        return ToolWriteFileInput

    def _previous_line_count(self, path: str) -> Optional[int]:
        try:
            return len(self._sandbox_env.read_file(path).splitlines())
        except FileNotFoundError:
            return None
        except ValueError:
            return -1

    def execute(self, input: ToolWriteFileInput) -> str:
        previous = self._previous_line_count(input.path)
        written = self._sandbox_env.write_file(input.path, input.content)
        line_count = len(input.content.splitlines())

        if previous is None:
            summary = f"Created {written} ({line_count} lines)."
        elif previous < 0:
            summary = f"Replaced {written} ({line_count} lines)."
        else:
            summary = f"Replaced {written} ({line_count} lines, previously {previous})."
        return summary + python_syntax_warning(written, input.content)
