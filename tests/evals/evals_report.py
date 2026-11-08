import json
import time
import pathlib
import statistics
import subprocess

from tests.evals.evals_runners.evals_record_base import EvalsRecordBase
from tests.evals.evals_runners.evals_runners_type import EvalsRunnersType


class EvalsReport:
    """Where an eval session writes what it measured: one directory per session under
    tests/evals/results/, named after when it started and the commit it ran on, so two
    sessions — before and after a change — sit side by side.

    Each record becomes one JSON line in <runner type>.jsonl, holding everything needed
    to read the run back later. Each case adds one line to summary.txt, which is also
    printed: yes/no fields as how many runs passed, numbers as their mean. The directory
    is git-ignored; results belong to a machine and a moment, not to the code.

    One report serves the whole session, shared by every eval module through shared(),
    so all of a session's results land in the same directory."""

    RESULTS_DIRECTORY = pathlib.Path(__file__).resolve().parent / "results"
    _shared = None

    def __init__(self) -> None:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output = True, text = True, check = False
        ).stdout.strip() or "unknown"
        self._directory: pathlib.Path = self.RESULTS_DIRECTORY / f"{time.strftime('%Y%m%d-%H%M%S')}-{commit}"

    @classmethod
    def shared(cls) -> "EvalsReport":
        if cls._shared is None:
            cls._shared = cls()
        return cls._shared

    @property
    def directory(self) -> pathlib.Path:
        return self._directory

    def _summarize(self, records: list[EvalsRecordBase], fields: list[str]) -> str:
        parts = []
        for current_field in fields:
            values = [getattr(current, current_field) for current in records if getattr(current, current_field) is not None]
            if not values:
                parts.append(f"{current_field}=-")
            elif all(isinstance(current, bool) for current in values):
                parts.append(f"{current_field}={sum(values)}/{len(values)}")
            else:
                parts.append(f"{current_field}={round(statistics.mean(values), 2)}")
        return " ".join(parts)

    def add(self, runner_type: EvalsRunnersType, case_id: str, records: list[EvalsRecordBase], fields: list[str]) -> str:
        self._directory.mkdir(parents = True, exist_ok = True)
        with (self._directory / f"{runner_type.value}.jsonl").open("a", encoding = "utf-8") as output:
            for current in records:
                output.write(current.model_dump_json() + "\n")

        line = f"{runner_type.value:10s} {case_id:26s} {self._summarize(records, fields)}"
        with (self._directory / "summary.txt").open("a", encoding = "utf-8") as output:
            output.write(line + "\n")
        print(f"\n{line}")
        return line
