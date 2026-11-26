from typing import Optional

from app.intelligence.agents import RagContext
from app.intelligence.agents import RagLayerBase
from app.intelligence.agents import RagLayerType
from app.intelligence.messages import MessageType
from app.intelligence.security import SecurityMonitor
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.security import SecurityPromptType


class RagSecurityLayer(RagLayerBase):
    """Inspects everything reranking and generation will read: the question for
    jailbreaking, and the earlier answers and the retrieved candidates for poisoning,
    since both were stored before this run and are read again by it. It runs right after
    retrieval, the first moment the candidates are known; only the query rewrite, which
    reads the question and the history, comes before it.

    Monitor mode, as in OperationSecurityLayer: findings go to the trace through a
    SecurityMonitor and into context.security, and nothing is changed or refused."""

    def __init__(self, tracing_service: Optional[TracingServiceBase] = None,
        security_monitor: Optional[SecurityMonitor] = None) -> None:
        self._security_monitor: SecurityMonitor = (
            security_monitor
            if security_monitor is not None
            else SecurityMonitor(tracing_service)
        )

    @property
    def layer_type(self) -> RagLayerType:
        return RagLayerType.SECURITY

    def _text_of(self, content: object) -> str:
        return content if isinstance(content, str) else str(content)

    def _source_of(self, entry: VectorDbMemoryEntry) -> str:
        title = entry.message.name or "an untitled document"
        if entry.metadata is None:
            return title
        return f"{title}, part {entry.metadata.source.chunk_index + 1}"

    def execute(self, context: RagContext) -> None:
        verdicts = [self._security_monitor.inspect(
            SecurityPromptType.JAILBREAKING, self._text_of(context.goal.content), "the user's question"
        )]
        verdicts.extend(
            self._security_monitor.inspect(
                SecurityPromptType.POISONING, self._text_of(current_message.content), "an earlier answer"
            )
            for current_message in context.history
            if current_message.type is MessageType.AI_MESSAGE
        )
        verdicts.extend(
            self._security_monitor.inspect(
                SecurityPromptType.POISONING, self._text_of(current_entry.message.content), self._source_of(current_entry)
            )
            for current_entry in context.candidates
        )
        context.security = [current_verdict for current_verdict in verdicts if current_verdict.flagged]
