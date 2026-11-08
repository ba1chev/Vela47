import re
import shlex
import posixpath

from app.intelligence.tools import ToolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.tools import ToolRunTestsInput
from app.intelligence.sandbox import SandboxCommandResult


class ToolRunTests(ToolBase[ToolRunTestsInput, str]):
    """Runs the workspace's tests with pytest inside the sandbox and reports the outcome.

    This is what turns a TEST subagent from writing tests into testing: it sees whether
    its assertions pass, and can fix a test that is wrong or report code that is. The
    command runs through the sandbox's run(), which on the Docker pool is a container
    with no network and capped memory, CPU and processes — model-written code never runs
    on the host. A sandbox that cannot run commands at all raises, and the agent is told
    why instead of being told its tests passed.

    The command is built here, never by the model: the path and keyword are confined to
    the workspace and shell-quoted, so the only thing the agent chooses is which tests.
    Bytecode and pytest's cache are switched off: the tests run on a copy of the
    workspace that is deleted when they finish, so writing either would only cost time.

    pytest's exit code says more than its output does at a glance, so the result leads
    with what the code means — failures, a broken import, nothing collected — then the
    summary line, then the output with its middle cut if it is long. The end of pytest's
    output is where the failures are explained, so more of it is kept than of the start."""

    TIMEOUT_SECONDS = 90
    HEAD_CHARS = 1_000
    TAIL_CHARS = 3_000
    SUMMARY_PATTERN = re.compile(r"\b\d+ (passed|failed|error|errors|skipped|deselected)\b")
    EXIT_MEANINGS = {
        0: "All tests passed.",
        1: "Some tests failed.",
        2: "The run was interrupted — usually a test file that fails to import or does not parse.",
        3: "pytest hit an internal error.",
        4: "pytest was called with a path or option it does not understand.",
        5: "No tests were collected — test files must be named test_*.py and test functions must start with test_."
    }

    def __init__(self, sandbox_env: SandboxEnv) -> None:
        super().__init__()
        self._sandbox_env: SandboxEnv = sandbox_env

    @property
    def name(self) -> str:
        return "run_tests"

    @property
    def description(self) -> str:
        return (
            "Run the tests in your workspace with pytest and get back whether they passed, "
            "with the failure details. Run them after writing or changing a test, and again "
            "after every fix."
        )

    @property
    def input_schema(self) -> type[ToolRunTestsInput]:
        return ToolRunTestsInput

    def _command(self, input: ToolRunTestsInput) -> str:
        arguments = [
            "python", "-m", "pytest", "-q", "--no-header", "--tb=short", "--color=no",
            "-p", "no:cacheprovider"
        ]
        if input.path and input.path.strip():
            target = posixpath.normpath(input.path.strip())
            if target.startswith("..") or posixpath.isabs(target):
                raise ValueError(f"Path '{input.path}' points outside the workspace and was refused.")
            arguments.append(target)
        if input.keyword and input.keyword.strip():
            arguments.extend(["-k", input.keyword.strip()])

        return "PYTHONDONTWRITEBYTECODE=1 " + " ".join(shlex.quote(current) for current in arguments)

    def _clip(self, output: str) -> str:
        if len(output) <= self.HEAD_CHARS + self.TAIL_CHARS:
            return output
        cut = len(output) - self.HEAD_CHARS - self.TAIL_CHARS
        return output[:self.HEAD_CHARS] + f"\n… {cut} characters cut …\n" + output[-self.TAIL_CHARS:]

    def _summary(self, output: str) -> str:
        for current_line in reversed(output.splitlines()):
            if self.SUMMARY_PATTERN.search(current_line):
                return current_line.strip("= ").strip()
        return ""

    def _verdict(self, result: SandboxCommandResult) -> str:
        if result.timed_out:
            return (
                f"The run was stopped after {self.TIMEOUT_SECONDS}s — look for an infinite loop "
                f"or a test waiting for input."
            )
        if "No module named pytest" in result.output:
            return "pytest is not installed in this sandbox, so the tests cannot be run."
        return self.EXIT_MEANINGS.get(result.exit_code, f"pytest exited with code {result.exit_code}.")

    def execute(self, input: ToolRunTestsInput) -> str:
        result = self._sandbox_env.run(self._command(input), timeout_seconds = self.TIMEOUT_SECONDS)
        summary = self._summary(result.output)
        headline = self._verdict(result) + (f" {summary}." if summary else "")
        return f"{headline}\n\n{self._clip(result.output)}"
