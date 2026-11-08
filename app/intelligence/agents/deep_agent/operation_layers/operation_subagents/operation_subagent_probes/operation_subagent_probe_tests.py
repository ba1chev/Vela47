import posixpath

from app.intelligence.tools import ToolRunTests
from app.intelligence.messages import MessageBase
from app.intelligence.tools import ToolRunTestsInput
from app.intelligence.agents import OperationSubagentProbeBase


class OperationSubagentProbeTests(OperationSubagentProbeBase):
    """Runs the workspace's tests once more after a step and reports the outcome pytest
    gave — whether or not the subagent ran them itself, and whatever it said they did.

    The run goes through ToolRunTests, the same command and the same sandbox the
    subagent's own run_tests uses, so the result is the one the subagent would have seen
    on its last run. Only the headline is kept — what the exit code means and pytest's
    summary line — since the merging layer needs the outcome, not the traceback.

    A workspace with no test file gets that said instead of a run, and a sandbox that
    cannot run commands — the local fallback without Docker — gets that said too: in
    both cases no test ran, and an answer must not claim one passed."""

    def _has_tests(self) -> bool:
        return any(
            posixpath.basename(current_path).startswith("test_") and current_path.endswith(".py")
            for current_path in self._sandbox_env.list_files()
        )

    def after(self, messages: list[MessageBase]) -> list[str]:
        if not self._has_tests():
            return ["No test file exists in the workspace, so no test was run."]
        try:
            output = ToolRunTests(self._sandbox_env).execute(ToolRunTestsInput())
        except RuntimeError:
            return ["The tests could not be run: this sandbox cannot run commands."]
        return [f"The system ran the tests after this step: {output.splitlines()[0]}"]
