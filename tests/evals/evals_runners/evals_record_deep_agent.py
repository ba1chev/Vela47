from pydantic import Field
from typing import Optional

from tests.evals.evals_runners.evals_record_base import EvalsRecordBase


class EvalsRecordDeepAgent(EvalsRecordBase):
    """One deep agent run, read from what it left behind: the plan and every report from
    its trace, its tool calls and their errors, the final answer, and the verdict of the
    case's hidden test on the code it wrote.

    The plan and the reports are kept whole, so a failed check can be read back and its
    cause found — a wrong step type, a report that was a raw tool call, an answer that
    repeated its report."""

    steps: list[dict[str, str]] = Field(
        description = "The plan as it ran: each step's subagent type and the instruction it was given."
    )
    reports: list[dict[str, str]] = Field(
        description = "What each subagent reported back, with the status its step ended in and the "
            "evidence the system's probes gathered on the step, one fact per line."
    )
    final: str = Field(
        description = "The answer the user would have received."
    )
    plan_ok: bool = Field(
        description = "Whether every step was of an allowed type and the required types appeared in order."
    )
    within_max_steps: bool = Field(
        description = "Whether the plan had at least one step and no more than the case allows."
    )
    names_kept: bool = Field(
        description = "Whether every step's instruction still named what the case is about."
    )
    tool_calls: int = Field(
        ge = 0,
        description = "How many tool calls the subagents made in the run."
    )
    tool_errors: int = Field(
        ge = 0,
        description = "How many of those tool calls ended in an error."
    )
    raw_tool_call_reports: int = Field(
        ge = 0,
        description = "Reports that held a tool call written out as text — a call nobody ran, passed "
            "on as if it were a finding."
    )
    echoes_report: bool = Field(
        description = "Whether the final answer repeated the report it was given instead of answering."
    )
    own_tests_passed: Optional[bool] = Field(
        default = None,
        description = "Whether the tests the agent wrote itself pass, run by the eval after the run. None "
            "when the case writes no code or the run crashed; false when the agent wrote no test."
    )
    claims_tests_passed: bool = Field(
        default = False,
        description = "Whether the final answer says the tests passed — it mentions tests and passing, and "
            "no failure, error or tests that did not run."
    )
    false_test_claim: bool = Field(
        default = False,
        description = "Whether the answer says the tests passed when the agent's own tests do not. Only "
            "counted for cases that write code."
    )
    hidden_test_passed: Optional[bool] = Field(
        default = None,
        description = "Whether the case's hidden test passed on the code the agent wrote. None when the "
            "case has no hidden test or the run crashed."
    )
    hidden_test_output: Optional[str] = Field(
        default = None,
        description = "The end of the hidden test's pytest output, to read why it failed."
    )
