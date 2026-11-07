from uuid import uuid4
from typing import Optional
from pydantic import BaseModel, Field, SerializeAsAny

from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageBase
from app.intelligence.messages import MessageHuman
from app.intelligence.memory import VectorDbMemoryEntry


class RagContext(BaseModel):
    """The single mutable object threaded through every layer of a RagPipeline — the
    RAG counterpart of OperationContext, with the same rule: each layer reads what its
    predecessors filled and writes the one field it owns. Query writes query, retrieval
    writes candidates, reranking writes passages and relevance, generation writes final.

    Keeping the whole state in one place is what lets generation cite a passage by the
    same number reranking judged it under, and what lets the trace report how many
    candidates survived each stage without any layer reporting it itself."""

    run_id: str = Field(
        default_factory = lambda: uuid4().hex[:12],
        description = "Identifies this run in the trace."
    )
    goal: MessageHuman = Field(
        description = "The question that started this run, exactly as it reached the RagAgent. "
            "Never overwritten, so generation answers it rather than the rewritten query."
    )
    history: list[SerializeAsAny[MessageBase]] = Field(
        default_factory = list,
        description = "Earlier turns of the conversation, oldest first, already bounded by the "
            "agent. The query layer reads them to make a follow-up searchable on its own, and "
            "generation reads them so the answer continues the conversation."
    )
    query: Optional[str] = Field(
        default = None,
        description = "The goal rewritten as a standalone search query — 'what about the second "
            "one?' turned into what the second one was. None until the query layer has run, in "
            "which case retrieval searches for the goal as written."
    )
    candidates: list[VectorDbMemoryEntry] = Field(
        default_factory = list,
        description = "Passages the hybrid search returned, best first. Many and approximate on "
            "purpose: retrieval casts the net, reranking decides."
    )
    passages: list[VectorDbMemoryEntry] = Field(
        default_factory = list,
        description = "The candidates that survived reranking, most relevant first — the sources "
            "generation answers from and cites by position."
    )
    relevance: dict[str, int] = Field(
        default_factory = dict,
        description = "The reranker's score, 0 to 10, for every candidate it judged, keyed by "
            "chunk id. Empty when reranking did not run or its reply could not be parsed."
    )
    final: Optional[MessageAI] = Field(
        default = None,
        description = "The answer the RagAgent returns, with its sources in response_metadata. "
            "None until generation has run."
    )
