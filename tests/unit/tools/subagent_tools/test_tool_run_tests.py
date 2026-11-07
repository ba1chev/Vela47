import pytest
import pathlib
import tempfile

from app.intelligence.tools import ToolRunTests
from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.tools import ToolRunTestsInput
from app.intelligence.sandbox import SandboxCommandResult
from tests.fixtures.sandbox.scripted_sandbox_env import ScriptedSandboxEnv


def make_tool(*results):
    return ToolRunTests(ScriptedSandboxEnv(pathlib.Path(tempfile.mkdtemp()) / "run", list(results)))


def result(exit_code, output, timed_out = False):
    return SandboxCommandResult(exit_code = exit_code, output = output, timed_out = timed_out)


class TestToolRunTests:
    def test_name_is_stable(self):
        assert make_tool().name == "run_tests"

    def test_pytest_runs_quietly_without_cache_or_bytecode(self):
        tool = make_tool()
        tool.execute(ToolRunTestsInput())
        command, timeout = tool._sandbox_env.commands[0]
        assert command == (
            "PYTHONDONTWRITEBYTECODE=1 python -m pytest -q --no-header --tb=short --color=no "
            "-p no:cacheprovider"
        )
        assert timeout == ToolRunTests.TIMEOUT_SECONDS

    def test_the_path_and_keyword_are_quoted_into_the_command(self):
        tool = make_tool()
        tool.execute(ToolRunTestsInput(path = "tests/test_sort.py", keyword = "empty and not slow; rm -rf /"))
        command = tool._sandbox_env.commands[0][0]
        assert command.endswith("tests/test_sort.py -k 'empty and not slow; rm -rf /'")

    def test_a_path_outside_the_workspace_is_refused_before_running(self):
        tool = make_tool()
        with pytest.raises(ValueError):
            tool.execute(ToolRunTestsInput(path = "../../etc"))
        assert tool._sandbox_env.commands == []

    def test_a_pass_leads_with_the_verdict_and_the_summary(self):
        output = make_tool(result(0, "...\n3 passed in 0.02s")).execute(ToolRunTestsInput())
        assert output.startswith("All tests passed. 3 passed in 0.02s.")

    def test_a_failure_keeps_the_details(self):
        failure = "F.\n___ test_sort ___\nassert [2, 1] == [1, 2]\n=== 1 failed, 1 passed in 0.03s ==="
        output = make_tool(result(1, failure)).execute(ToolRunTestsInput())
        assert output.startswith("Some tests failed. 1 failed, 1 passed in 0.03s.")
        assert "assert [2, 1] == [1, 2]" in output

    def test_nothing_collected_explains_the_naming_convention(self):
        output = make_tool(result(5, "no tests ran in 0.01s")).execute(ToolRunTestsInput())
        assert "test_*.py" in output

    def test_an_import_error_is_read_as_an_interrupted_run(self):
        assert "fails to import" in make_tool(result(2, "ImportError")).execute(ToolRunTestsInput())

    def test_a_missing_pytest_is_named(self):
        output = make_tool(result(1, "/usr/local/bin/python: No module named pytest")).execute(ToolRunTestsInput())
        assert output.startswith("pytest is not installed")

    def test_a_timeout_is_named(self):
        output = make_tool(result(-1, "Command exceeded 90s", timed_out = True)).execute(ToolRunTestsInput())
        assert output.startswith("The run was stopped after 90s")

    def test_long_output_keeps_its_end(self):
        long_output = "start\n" + "x" * 10_000 + "\nFAILED tests/test_a.py::test_b - assert 1 == 2\n1 failed in 0.1s"
        output = make_tool(result(1, long_output)).execute(ToolRunTestsInput())
        assert "characters cut" in output and output.endswith("1 failed in 0.1s") and "start" in output

    def test_a_sandbox_that_cannot_run_commands_raises_its_reason(self):
        tool = ToolRunTests(SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / "run"))
        with pytest.raises(RuntimeError, match = "cannot run commands"):
            tool.execute(ToolRunTestsInput())
