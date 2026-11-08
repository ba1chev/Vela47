import pathlib
import tempfile

from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.sandbox import SandboxCommandResult
from app.intelligence.agents import OperationSubagentProbeTests
from tests.fixtures.sandbox.scripted_sandbox_env import ScriptedSandboxEnv

TEST_FILE = {"tests/test_primes.py": "def test_x():\n    assert True\n"}


def make_probe(files = None, *results):
    env = ScriptedSandboxEnv(pathlib.Path(tempfile.mkdtemp()) / "run", list(results))
    for current_path, current_content in (files or {}).items():
        env.write_file(current_path, current_content)
    return OperationSubagentProbeTests(env), env


class TestOperationSubagentProbeTests:
    def test_the_tests_are_run_and_their_outcome_reported(self):
        probe, env = make_probe(TEST_FILE, SandboxCommandResult(exit_code = 1, output = "1 failed, 2 passed in 0.03s"))
        fact = probe.after([])[0]
        assert fact.startswith("The system ran the tests after this step: Some tests failed.") and "1 failed, 2 passed" in fact
        assert len(env.commands) == 1

    def test_passing_tests_are_reported_as_passing(self):
        probe, _ = make_probe(TEST_FILE)
        assert probe.after([])[0].startswith("The system ran the tests after this step: All tests passed.")

    def test_without_a_test_file_nothing_is_run(self):
        probe, env = make_probe({"primes.py": "x = 1\n"})
        assert probe.after([]) == ["No test file exists in the workspace, so no test was run."] and env.commands == []

    def test_a_sandbox_that_cannot_run_commands_is_reported(self):
        env = SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / "run")
        env.write_file("tests/test_primes.py", "def test_x():\n    assert True\n")
        assert OperationSubagentProbeTests(env).after([]) == ["The tests could not be run: this sandbox cannot run commands."]
