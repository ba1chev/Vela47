from pydantic import Field
from typing import Optional

from app.intelligence.agents import OperationSubagentType
from tests.evals.evals_cases.evals_case_base import EvalsCaseBase


class EvalsCaseDeepAgent(EvalsCaseBase):
    """A request the deep agent is evaluated on, and what a good run of it looks like.

    The plan is judged by the kinds of step it uses rather than by its wording: every
    step must be one of allowed_types, and required_types must all appear, in that
    order — CODE before TEST, never the other way round. names_pattern is what every
    step must still mention for the work to be about the right thing.

    A hidden test, when the case has one, is run against the code the agent wrote, in a
    copy of its workspace after the run. The agent never sees it, so passing it means
    the code works — not that the agent says it does."""

    goal: str = Field(
        description = "The request, exactly as a user would send it — typos included, since "
            "keeping a misspelled name is part of what is measured."
    )
    allowed_types: frozenset[OperationSubagentType] = Field(
        description = "The only kinds of step a good plan for this request uses."
    )
    required_types: tuple[OperationSubagentType, ...] = Field(
        description = "Kinds of step a good plan must contain, in the order they must first appear."
    )
    max_steps: int = Field(
        ge = 1,
        description = "Most steps the request justifies; a longer plan is splitting one job "
            "into overlapping ones."
    )
    names_pattern: str = Field(
        description = "Regular expression, matched case-insensitively, that every step's "
            "instruction must match — the names the work is about."
    )
    hidden_test_file: Optional[str] = Field(
        default = None,
        description = "File the agent must write for the hidden test to import, such as "
            "'primes.py'. None when the case writes no code."
    )
    hidden_test_code: Optional[str] = Field(
        default = None,
        description = "A pytest module run in a copy of the agent's workspace after the run, "
            "never shown to the agent. None when the case writes no code."
    )
