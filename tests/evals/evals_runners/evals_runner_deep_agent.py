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
    workspace: after the run, the case's hidden test is copied next to it, in a copy of
    the run's directory, and run in the sandbox like any test.

    The pool is the runner's own. Its containers are named vela47-eval-*, so they never
    collide with the server's vela47-slot-*, and they are removed when the process
    exits. Three are enough: the evals run one case at a time, and the subagents of a
    run one after another."""

    POOL_SIZE = 3
    NAME_PREFIX = "vela47-eval"
    HIDDEN_TEST_FILE = "test_hidden_eval_check.py"
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
        self._pool = SandboxPoolDocker(
            size = self.POOL_SIZE,
            name_prefix = self.NAME_PREFIX,
            base_directory = pathlib.Path(tempfile.mkdtemp(prefix = "vela47-eval-"))
        )
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

    def _hidden_test(self, directories: set[str], case: EvalsCaseDeepAgent) -> tuple[bool, str]:
        workspace = next(
            (
                self._pool.base_directory / current
                for current in directories
                if (self._pool.base_directory / current / case.hidden_test_file).exists()
            ),
            None
        )
        if workspace is None:
            return False, f"{case.hidden_test_file} was not written."

        copy_id = f"hidden-{workspace.name}"
        shutil.copytree(workspace, self._pool.base_directory / copy_id)
        (self._pool.base_directory / copy_id / self.HIDDEN_TEST_FILE).write_text(case.hidden_test_code)
        slot = self._pool.acquire()
        try:
            result = self._pool.env_for(slot, copy_id).run(
                f"python -m pytest -q -p no:cacheprovider {self.HIDDEN_TEST_FILE}", timeout_seconds = 60
            )
        finally:
            self._pool.release(slot)
        return result.exit_code == 0, result.output[-600:]

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
            {"status": str(current.payload.get("status")), "result": str(current.payload.get("result", ""))}
            for current in events if current.type is TraceEventType.SUBAGENT_FINISHED
        ]
        tool_statuses = [current.payload.get("status") for current in events if current.type is TraceEventType.TOOL_EXECUTED]
        types = [OperationSubagentType[current["type"]] for current in steps]
        new_directories = {current for current in self._run_directories() - before if not current.startswith("hidden-")}
        hidden = self._hidden_test(new_directories, case) if case.hidden_test_file and crashed is None else None

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
            hidden_test_passed = hidden[0] if hidden else None,
            hidden_test_output = hidden[1] if hidden else None
        )
