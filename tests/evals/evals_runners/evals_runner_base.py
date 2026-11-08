import ollama
import pytest
import subprocess
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from tests.evals.evals_cases.evals_case_base import EvalsCaseBase
from tests.evals.evals_runners.evals_record_base import EvalsRecordBase
from tests.evals.evals_runners.evals_runners_type import EvalsRunnersType

TCase = TypeVar("TCase", bound = EvalsCaseBase)
TRecord = TypeVar("TRecord", bound = EvalsRecordBase)


class EvalsRunnerBase(ABC, Generic[TCase, TRecord]):
    """Abstract base for running one agent, for real, on an eval case and turning each
    run into a record of what it measurably did. TCase is what the runner is asked to
    do and TRecord what it reports back — both Pydantic models, so a record can be
    written as a JSON line and read back without the runner.

    Everything a run is measured by comes from what it left behind — the trace, the
    answer, the files it wrote — never from what the agent says about its own work.

    Building a runner costs nothing; start() does what a whole session shares and
    costs seconds — containers to start, documents to embed — and run_all() calls it
    the first time it is needed. That keeps a test module free to build its runner on
    import, which the unit suite does when it collects the module only to deselect it.

    A service the agent needs that is not running skips the calling eval rather than
    failing it: without the model or the sandbox there is nothing to measure, which is
    not the same as something being wrong."""

    def __init__(self) -> None:
        self._started: bool = False

    @property
    @abstractmethod
    def runner_type(self) -> EvalsRunnersType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def run(self, case: TCase, run: int) -> TRecord:
        raise NotImplementedError("Must be implemented")

    def shutdown(self) -> None:
        return None

    def run_all(self, case: TCase, runs: int) -> list[TRecord]:
        if not self._started:
            self.start()
            self._started = True
        return [self.run(case, current_run) for current_run in range(runs)]

    def _require_ollama(self) -> None:
        try:
            ollama.list()
        except Exception:
            pytest.skip("Ollama is not reachable, so the agent cannot be evaluated.")

    def _require_docker(self) -> None:
        try:
            reachable = subprocess.run(["docker", "info"], capture_output = True, timeout = 10, check = False).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            reachable = False
        if not reachable:
            pytest.skip("Docker is not reachable, so the agent's sandbox cannot run.")
