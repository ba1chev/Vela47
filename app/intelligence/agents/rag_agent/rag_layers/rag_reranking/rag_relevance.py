from pydantic import Field, RootModel

from app.intelligence.agents import RagRelevanceScore


class RagRelevance(RootModel[list[RagRelevanceScore]]):
    """The reranker's structured reply — one score per passage. Doubles as the JSON
    schema handed to the reranking model, as OperationPlan does for the planner, so what
    the model is asked to produce and what is parsed can never drift apart.

    It is a bare list rather than an object holding one, because that is what a small
    model writes when it is asked for scores: wrapped in an object, qwen3:1.7b scored
    every passage correctly and still failed validation by leaving the wrapper out. The
    contract follows the shape the model produces instead of retrying until it complies."""

    root: list[RagRelevanceScore] = Field(
        description = "One entry per passage that was shown, in any order."
    )
