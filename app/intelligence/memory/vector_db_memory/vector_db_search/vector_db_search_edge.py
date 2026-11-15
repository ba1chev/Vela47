from collections.abc import Hashable
from pydantic import BaseModel, Field


class VectorDBSearchEdge(BaseModel):
    """One outgoing edge of a weighted graph: the node it leads to and what it costs to
    follow it. Weighted graphs are dicts from a node to the list of its edges, and are
    what uniform cost search and every informed search walk."""

    model_config = {"frozen": True}

    to: Hashable = Field(description = "The node this edge leads to.")
    weight: float = Field(
        description = "The cost of following this edge. Path costs are the sum of the "
            "weights along the path, so weights are expected to be non-negative."
    )
