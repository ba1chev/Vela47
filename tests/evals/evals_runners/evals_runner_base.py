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
    """Abstract base for running one agent for real on an eval case and recording what
    it measurably did. TCase and TRecord are Pydantic models, so records are written and
    read back as JSON lines. Everything is measured from what a run left behind (trace,
    answer, files), never from what the agent says about itself.

    Building a runner costs nothing; start() does the expensive shared work and
    run_all() calls it when first needed, so a test module can build its runner on
    import. A missing service skips the eval rather than failing it: there is nothing to
    measure, which is not the same as something being wrong."""

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
