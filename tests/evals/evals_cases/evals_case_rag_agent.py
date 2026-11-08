from pydantic import Field

from tests.evals.evals_cases.evals_case_base import EvalsCaseBase


class EvalsCaseRagAgent(EvalsCaseBase):
    """A question the RAG agent is evaluated on, over EVALS_DOCUMENTS_RAG_AGENT.

    facts are what the answer must contain, written the way the documents write them.
    An unanswerable question has none: the documents do not cover it, and a good answer
    says so without citing anything. history holds the earlier turns of a follow-up
    that only makes sense after them."""

    question: str = Field(
        description = "The question, exactly as a user would ask it."
    )
    facts: tuple[str, ...] = Field(
        default = (),
        description = "Regular expressions, matched case-insensitively, that the answer must all "
            "match — the key facts. Empty for a question the documents do not cover."
    )
    answerable: bool = Field(
        description = "Whether the documents answer the question. An unanswerable question must be "
            "declined without a citation."
    )
    language: str = Field(
        description = "Language the answer must be written in: 'bg' for Bulgarian, anything else "
            "for a language written in Latin script."
    )
    history: tuple[tuple[str, str], ...] = Field(
        default = (),
        description = "Earlier (question, answer) turns restored into the agent before the question "
            "is asked, for a follow-up that refers back to them."
    )
