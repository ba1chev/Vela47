import posixpath

from app.intelligence.tools import ToolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.tools import ToolWriteTestInput


class ToolWriteTest(ToolBase[ToolWriteTestInput, str]):
    """Writes a test file, placed where a runner will find it.

    Distinct from ToolWriteFile only in that it enforces the discovery convention:
    under tests/ with a test_ prefix. That is not cosmetic — a test saved under a
    name no runner collects is an artefact nobody will ever execute, and the agent
    writing it has no way to notice.

    It writes but does not run. The sandbox is capable of running commands, so this
    is a deliberate limit rather than a technical one: the artefact is left for a
    later stage to execute, which means the subagent never sees whether its test
    passes. Lifting that is a matter of giving this tool the sandbox's run()."""

    TESTS_DIRECTORY = "tests"
    TEST_PREFIX = "test_"

    def __init__(self, sandbox_env: SandboxEnv) -> None:
        super().__init__()
        self._sandbox_env: SandboxEnv = sandbox_env

    @property
    def name(self) -> str:
        return "write_test"

    @property
    def description(self) -> str:
        return (
            "Write a test file into your workspace. Use it to turn the cases you "
            "identified into runnable assertions — concrete inputs and expected "
            "outputs, not prose about what ought to be tested."
        )

    @property
    def input_schema(self) -> type[ToolWriteTestInput]:
        return ToolWriteTestInput

    def _normalise(self, path: str) -> str:
        name = posixpath.basename(path.strip().strip("/")) or "test_generated.py"

        if not name.endswith(".py"):
            name = f"{name}.py"
        if not name.startswith(self.TEST_PREFIX):
            name = f"{self.TEST_PREFIX}{name}"

        return posixpath.join(self.TESTS_DIRECTORY, name)

    def execute(self, input: ToolWriteTestInput) -> str:
        target = self._normalise(input.path)
        written = self._sandbox_env.write_file(target, input.content)
        line_count = len(input.content.splitlines())

        if written != input.path:
            return (
                f"Wrote {written} ({line_count} lines) — renamed from '{input.path}' "
                f"so a test runner will discover it."
            )
        return f"Wrote {written} ({line_count} lines)."
