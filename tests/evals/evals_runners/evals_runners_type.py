from enum import Enum


class EvalsRunnersType(str, Enum):
    """Enumerates the agents an eval can run. The value also names the file an eval
    session writes that agent's records to, so results from different agents never
    share a file.

    DEEP_AGENT runs the planner, the subagents in a Docker sandbox and the merger.
    RAG_AGENT runs query rewriting, retrieval, reranking and generation over documents
    the runner indexes itself."""

    DEEP_AGENT = "deep_agent"
    RAG_AGENT = "rag_agent"
