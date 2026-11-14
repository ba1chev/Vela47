import pathlib
import tempfile

from app.intelligence.sandbox import SandboxLambda
from app.intelligence.sandbox import SANDBOX_OUTPUT_MAX_CHARS
from tests.fixtures.sandbox.stub_lambda_client import StubLambdaClient


def make_env(client, run_id = "run-a"):
    return SandboxLambda("vela47-sandbox", pathlib.Path(tempfile.mkdtemp()) / run_id, client, "lambda-slot-0")


class TestSandboxLambda:
    def test_files_stay_in_the_runs_directory(self):
        env = make_env(StubLambdaClient())
        env.write_file("sort.py", "x = 1\n")
        assert (env.root / "sort.py").read_text() == "x = 1\n" and env.list_files() == ["sort.py"]

    def test_a_command_reaches_the_function_with_the_runs_files(self):
        client = StubLambdaClient()
        env = make_env(client)
        env.write_file("sort.py", "x = 1\n")
        env.write_file("tests/test_sort.py", "from sort import x\n")
        env.run("python -m pytest -q", timeout_seconds = 30)
        assert client.requests == [{
            "function": "vela47-sandbox", "command": "python -m pytest -q", "timeout_seconds": 30,
            "files": {"./sort.py": "x = 1\n", "./tests/test_sort.py": "from sort import x\n"}
        }]

    def test_the_answer_becomes_the_result(self):
        result = make_env(StubLambdaClient({"exit_code": 1, "output": "1 failed\n", "timed_out": False})).run("pytest")
        assert (result.exit_code, result.output, result.timed_out) == (1, "1 failed", False)

    def test_a_timeout_is_reported_as_one(self):
        result = make_env(StubLambdaClient({"exit_code": -1, "output": "Command exceeded 60s", "timed_out": True})).run("sleep 99")
        assert result.timed_out and result.exit_code == -1

    def test_long_output_keeps_a_head_and_the_tail(self):
        output = "h" * 3000 + "m" * 20000 + "the verdict"
        result = make_env(StubLambdaClient({"exit_code": 0, "output": output, "timed_out": False})).run("pytest")
        assert len(result.output) < SANDBOX_OUTPUT_MAX_CHARS + 100 and result.output.endswith("the verdict")

    def test_a_failing_function_is_a_result_not_an_exception(self):
        result = make_env(StubLambdaClient(failure = "Task timed out after 90.00 seconds")).run("pytest")
        assert result.exit_code == -1 and "Task timed out after 90.00 seconds" in result.output

    def test_an_unreachable_function_is_a_result_not_an_exception(self):
        result = make_env(StubLambdaClient(unreachable = True)).run("pytest")
        assert result.exit_code == -1 and "could not be reached" in result.output

    def test_a_workspace_over_the_request_limit_is_refused_before_sending(self):
        client = StubLambdaClient()
        env = make_env(client)
        env.MAX_PAYLOAD_BYTES = 100
        env.write_file("big.txt", "x" * 1000)
        result = env.run("pytest")
        assert result.exit_code == -1 and "too large" in result.output and client.requests == []
