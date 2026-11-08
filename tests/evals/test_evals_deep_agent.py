import math
import pytest

from tests.evals.evals_report import EvalsReport
from tests.evals.evals_settings import EVALS_RUNS
from tests.evals.evals_runners.evals_runners_type import EvalsRunnersType
from tests.evals.evals_cases.evals_cases_deep_agent import EVALS_CASES_DEEP_AGENT
from tests.evals.evals_runners.evals_runners_factory.evals_runners_factory import EvalsRunnersFactory

pytestmark = pytest.mark.evals

RUNNER = EvalsRunnersFactory().create(EvalsRunnersType.DEEP_AGENT)
SUMMARY_FIELDS = [
    "plan_ok", "within_max_steps", "names_kept", "hidden_test_passed", "echoes_report",
    "raw_tool_call_reports", "tool_calls", "tool_errors", "elapsed"
]


def run_case(case_id):
    case = next(current for current in EVALS_CASES_DEEP_AGENT if current.id == case_id)
    records = RUNNER.run_all(case, EVALS_RUNS)
    EvalsReport.shared().add(RUNNER.runner_type, case_id, records, SUMMARY_FIELDS)
    return records


def count(records, field):
    return sum(bool(getattr(current, field)) for current in records)


def most(records):
    return math.ceil(2 * len(records) / 3)


def assert_sound(records):
    assert count(records, "crashed") == 0
    assert count(records, "raw_tool_call_reports") == 0
    assert count(records, "plan_ok") >= most(records)
    assert count(records, "within_max_steps") >= most(records)
    assert count(records, "echoes_report") <= len(records) - most(records)


class TestEvalsDeepAgent:
    """Runs the deep agent on each case EVALS_RUNS times (3 unless VELA47_EVALS_RUNS says
    otherwise) against the real local model and Docker sandbox, and checks only what can
    be measured without an opinion: no crash, no raw tool call passed off as a report,
    a plan made of the right kinds of steps and not too many of them, an answer that
    does not repeat its report, and code that passes a hidden test.

    The model is not deterministic, so a check passes when two thirds of the runs pass
    it — one bad run in three is the model, three bad runs in three is the system. The
    thresholds are what the agent achieved when they were set (2026-11-08). Two things
    are recorded but not asserted, because the small model fails them whatever the
    pipeline does: keeping the misspelled name 'amunset' in a plan, and the hidden test
    for slugify, whose code it writes without collapsing runs of spaces."""

    def test_a_plan_for_an_event_is_only_researched(self):
        assert_sound(run_case("hackathon"))

    def test_code_with_tests_is_written_then_tested_and_works(self):
        records = run_case("is_prime")
        assert_sound(records)
        assert count(records, "hidden_test_passed") >= most(records)

    def test_a_factual_question_is_only_researched(self):
        assert_sound(run_case("python_version"))

    def test_code_to_review_is_written_then_reviewed(self):
        assert_sound(run_case("slugify"))

    def test_a_question_in_bulgarian_is_only_researched(self):
        assert_sound(run_case("question_in_bulgarian"))
