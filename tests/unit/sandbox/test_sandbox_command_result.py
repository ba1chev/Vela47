from app.intelligence.sandbox import SandboxCommandResult


class TestSandboxCommandResult:
    def test_defaults_to_not_timed_out(self):
        assert SandboxCommandResult(exit_code = 0, output = "ok").timed_out is False

    def test_non_zero_exit_is_a_result_not_an_error(self):
        result = SandboxCommandResult(exit_code = 1, output = "boom")
        assert result.exit_code == 1 and result.output == "boom"

    def test_timeout_is_distinct_from_failure(self):
        result = SandboxCommandResult(exit_code = -1, output = "gave up", timed_out = True)
        assert result.timed_out is True
