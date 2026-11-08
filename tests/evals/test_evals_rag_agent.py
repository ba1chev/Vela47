import math
import pytest

from tests.evals.evals_report import EvalsReport
from tests.evals.evals_settings import EVALS_RUNS
from tests.evals.evals_runners.evals_runners_type import EvalsRunnersType
from tests.evals.evals_cases.evals_cases_rag_agent import EVALS_CASES_RAG_AGENT
from tests.evals.evals_runners.evals_runners_factory.evals_runners_factory import EvalsRunnersFactory

pytestmark = pytest.mark.evals

RUNNER = EvalsRunnersFactory().create(EvalsRunnersType.RAG_AGENT)
SUMMARY_FIELDS = ["facts_found", "cites", "language_ok", "reranked", "sources", "elapsed"]


def run_case(case_id):
    case = next(current for current in EVALS_CASES_RAG_AGENT if current.id == case_id)
    records = RUNNER.run_all(case, EVALS_RUNS)
    EvalsReport.shared().add(RUNNER.runner_type, case_id, records, SUMMARY_FIELDS)
    return records


def count(records, field):
    return sum(bool(getattr(current, field)) for current in records)


def most(records):
    return math.ceil(2 * len(records) / 3)


def assert_answered(records):
    assert count(records, "crashed") == 0
    assert count(records, "facts_found") >= most(records)
    assert count(records, "cites") >= most(records)
    assert count(records, "language_ok") >= most(records)
    assert all(current.reranked is not False for current in records)


def assert_declined(records):
    assert count(records, "crashed") == 0
    assert count(records, "cites") <= len(records) - most(records)
    assert count(records, "language_ok") >= most(records)


class TestEvalsRagAgent:
    """Runs the RAG agent on each case EVALS_RUNS times over EVALS_DOCUMENTS_RAG_AGENT,
    with the real embedding, reranking and generation models.

    An answerable question must be answered with its key facts, cite a source, be
    written in the question's language and carry only sources the reranker scored. An
    unanswerable one must be declined in the question's language without citing
    anything. As for the deep agent, two runs in three must pass; when the thresholds
    were set (2026-11-08) every run passed every check."""

    def test_an_error_code_is_explained_from_the_runbook(self):
        assert_answered(run_case("error_code"))

    def test_a_bulgarian_question_over_english_documents_is_answered_in_bulgarian(self):
        assert_answered(run_case("bulgarian_over_english"))

    def test_a_follow_up_is_resolved_against_the_earlier_turn(self):
        assert_answered(run_case("follow_up"))

    def test_two_facts_from_one_section_are_both_answered(self):
        assert_answered(run_case("two_facts"))

    def test_a_question_the_documents_do_not_cover_is_declined(self):
        assert_declined(run_case("unanswerable"))

    def test_a_bulgarian_question_the_documents_do_not_cover_is_declined_in_bulgarian(self):
        assert_declined(run_case("unanswerable_in_bulgarian"))
