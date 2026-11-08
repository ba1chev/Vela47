from pydantic import Field
from typing import Optional

from tests.evals.evals_runners.evals_record_base import EvalsRecordBase


class EvalsRecordRagAgent(EvalsRecordBase):
    """One RAG agent run, checked against the answer itself: whether it holds every
    expected fact, whether it cites a source, whether it is written in the language the
    case asks for, and whether every source it carries was scored by the reranker."""

    answer: str = Field(
        description = "The answer the user would have received."
    )
    sources: int = Field(
        ge = 0,
        description = "How many sources the answer carried in its response metadata."
    )
    facts_found: bool = Field(
        description = "Whether the answer matched every fact the case expects. Always true for a case "
            "that expects none."
    )
    cites: bool = Field(
        description = "Whether the answer cites a source as [n]."
    )
    language_ok: bool = Field(
        description = "Whether the answer is written in the language the case asks for, told apart by "
            "script: mostly Cyrillic for Bulgarian, almost none for anything else."
    )
    reranked: Optional[bool] = Field(
        default = None,
        description = "Whether every source the answer carries was scored by the reranker — a source "
            "without a score means its reply could not be read. None when there were no sources."
    )
