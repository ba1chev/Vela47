import re
import time
import atexit
import shutil
import pathlib
import tempfile
from typing import Optional

from app.intelligence.web import WebFetcher
from app.server.builders import build_deep_agent
from app.intelligence.messages import MessageHuman
from app.intelligence.tracing import TracingService
from app.intelligence.tracing import TraceEventType
from app.intelligence.sandbox import SandboxPoolDocker
from app.intelligence.agents import OperationSubagentType
from tests.evals.evals_runners.evals_runner_base import EvalsRunnerBase
from tests.evals.evals_runners.evals_runners_type import EvalsRunnersType
from tests.evals.evals_cases.evals_case_deep_agent import EvalsCaseDeepAgent
from tests.evals.evals_runners.evals_record_deep_agent import EvalsRecordDeepAgent


class EvalsRunnerDeepAgent(EvalsRunnerBase[EvalsCaseDeepAgent, EvalsRecordDeepAgent]):
    """Runs the real deep agent — the server's builder, the local model, the web and a
    Docker sandbox pool of its own — on an eval case.

    The plan is read from the trace's SUBAGENT_STARTED events, each report from
    SUBAGENT_FINISHED and the tool calls from TOOL_EXECUTED. The code is read from the
    workspace: after the run, the agent's own tests are run in a copy of the run's
    directory, then the case's hidden test is copied next to them and run too. The first
    says whether the answer may claim its tests pass; the second whether the code works.

    The pool is the server's compose project, brought up by the runner and brought down
    when the process exits. Its containers have the server's names and addresses, so the
    evals and the server cannot run at the same time."""

    HIDDEN_TEST_FILE = "test_hidden_eval_check.py"
    TESTS_MENTION = re.compile(r"\btests?\b", re.IGNORECASE)
    TESTS_PASS = re.compile(r"\bpass(ed|es|ing)?\b|\bsucceed(ed|s)?\b", re.IGNORECASE)
    TESTS_NOT_PASSING = re.compile(
        r"\bfail(ed|s|ing|ures?)?\b|\berrors?\b|\bnot (been )?run\b|\bdid not run\b|\bcould not (be )?run\b|\bno tests?\b",
        re.IGNORECASE
    )
    REPORT_ECHO = re.compile(r"The user's request:|The workers' reports|^Step \d+ \(|^Report \((success|error)\)", re.MULTILINE)

    def __init__(self) -> None:
        super().__init__()
        self._pool: Optional[SandboxPoolDocker] = None

    @property
    def runner_type(self) -> EvalsRunnersType:
        return EvalsRunnersType.DEEP_AGENT

    def start(self) -> None:
        self._require_ollama()
        self._require_docker()
        self._pool = SandboxPoolDocker(base_directory = pathlib.Path(tempfile.mkdtemp(prefix = "vela47-eval-")))
        self._pool.start()
        atexit.register(self.shutdown)

    def shutdown(self) -> None:
        if self._pool is not None:
            self._pool.shutdown()

    def _run_directories(self) -> set[str]:
        return {current.name for current in self._pool.base_directory.iterdir()}

    def _plan_ok(self, types: list[OperationSubagentType], case: EvalsCaseDeepAgent) -> bool:
        if not types or not set(types) <= case.allowed_types:
            return False
        positions = [types.index(current) if current in types else -1 for current in case.required_types]
        return -1 not in positions and positions == sorted(positions)

    def _claims_tests_passed(self, final: str) -> bool:
        return bool(self.TESTS_MENTION.search(final) and self.TESTS_PASS.search(final) and not self.TESTS_NOT_PASSING.search(final))

    def _run_in_copy(self, copy_id: str, command: str):
        slot = self._pool.acquire()
        try:
            return self._pool.env_for(slot, copy_id).run(command, timeout_seconds = 60)
        finally:
            self._pool.release(slot)

    def _check_code(self, directories: set[str], case: EvalsCaseDeepAgent) -> tuple[bool, bool, str]:
        workspace = next(
            (
                self._pool.base_directory / current
                for current in directories
                if (self._pool.base_directory / current / case.hidden_test_file).exists()
            ),
            None
        )
        if workspace is None:
            return False, False, f"{case.hidden_test_file} was not written."

        copy_id = f"hidden-{workspace.name}"
        shutil.copytree(workspace, self._pool.base_directory / copy_id)
        own = self._run_in_copy(copy_id, "python -m pytest -q -p no:cacheprovider")
        (self._pool.base_directory / copy_id / self.HIDDEN_TEST_FILE).write_text(case.hidden_test_code)
        hidden = self._run_in_copy(copy_id, f"python -m pytest -q -p no:cacheprovider {self.HIDDEN_TEST_FILE}")
        return own.exit_code == 0, hidden.exit_code == 0, hidden.output[-600:]

    def run(self, case: EvalsCaseDeepAgent, run: int) -> EvalsRecordDeepAgent:
        tracer = TracingService()
        before = self._run_directories()
        started = time.monotonic()
        try:
            final = build_deep_agent(tracer, self._pool, WebFetcher(), []).execute(MessageHuman(content = case.goal)).content
            crashed = None
        except Exception as error:
            final, crashed = "", f"{type(error).__name__}: {str(error)[:300]}"
        elapsed = time.monotonic() - started

        events = tracer.events()
        steps = [
            {"type": current.label, "instruction": str(current.payload.get("instruction", ""))}
            for current in events if current.type is TraceEventType.SUBAGENT_STARTED
        ]
        reports = [
            {
                "status": str(current.payload.get("status")),
                "result": str(current.payload.get("result", "")),
                "evidence": "\n".join(current.payload.get("evidence") or [])
            }
            for current in events if current.type is TraceEventType.SUBAGENT_FINISHED
        ]
        tool_statuses = [current.payload.get("status") for current in events if current.type is TraceEventType.TOOL_EXECUTED]
        types = [OperationSubagentType[current["type"]] for current in steps]
        new_directories = {current for current in self._run_directories() - before if not current.startswith("hidden-")}
        checked = self._check_code(new_directories, case) if case.hidden_test_file and crashed is None else None
        claims_tests_passed = self._claims_tests_passed(final)

        return EvalsRecordDeepAgent(
            case = case.id,
            run = run,
            elapsed = round(elapsed, 1),
            crashed = crashed,
            steps = steps,
            reports = reports,
            final = final,
            plan_ok = crashed is None and self._plan_ok(types, case),
            within_max_steps = 0 < len(steps) <= case.max_steps,
            names_kept = bool(steps) and all(re.search(case.names_pattern, current["instruction"], re.IGNORECASE) for current in steps),
            tool_calls = len(tool_statuses),
            tool_errors = tool_statuses.count("error"),
            raw_tool_call_reports = sum("<tool_call>" in current["result"] for current in reports),
            echoes_report = bool(self.REPORT_ECHO.search(final)),
            own_tests_passed = checked[0] if checked else None,
            claims_tests_passed = claims_tests_passed,
            false_test_claim = checked is not None and claims_tests_passed and not checked[0],
            hidden_test_passed = checked[1] if checked else None,
            hidden_test_output = checked[2] if checked else None
        )
