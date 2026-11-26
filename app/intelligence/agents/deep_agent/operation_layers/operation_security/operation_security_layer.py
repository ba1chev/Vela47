from typing import Optional

from app.intelligence.messages import MessageType
from app.intelligence.agents import OperationType
from app.intelligence.agents import OperationContext
from app.intelligence.security import SecurityMonitor
from app.intelligence.agents import OperationLayerBase
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.security import SecurityPromptType


class OperationSecurityLayer(OperationLayerBase):
    """Inspects what a run starts from before any model reads it: the user's request for
    jailbreaking, and every earlier answer of the conversation for poisoning, since
    planning and merging read those answers again on every turn. What tools bring back
    later is inspected where it arrives, in ToolExecutor.

    Monitor mode: findings go to the trace through a SecurityMonitor and into
    context.security, and nothing is changed or refused, so the layers after it run as
    they would without it. It calls no model and takes a fraction of a millisecond."""

    def __init__(self, tracing_service: Optional[TracingServiceBase] = None,
        security_monitor: Optional[SecurityMonitor] = None) -> None:
        self._security_monitor: SecurityMonitor = (
            security_monitor
            if security_monitor is not None
            else SecurityMonitor(tracing_service)
        )

    @property
    def operation_type(self) -> OperationType:
        return OperationType.SECURITY

    def _text_of(self, content: object) -> str:
        return content if isinstance(content, str) else str(content)

    def execute(self, context: OperationContext) -> None:
        verdicts = [self._security_monitor.inspect(
            SecurityPromptType.JAILBREAKING, self._text_of(context.goal.content), "the user's request"
        )]
        verdicts.extend(
            self._security_monitor.inspect(
                SecurityPromptType.POISONING, self._text_of(current_message.content), "an earlier answer"
            )
            for current_message in context.history
            if current_message.type is MessageType.AI_MESSAGE
        )
        context.security = [current_verdict for current_verdict in verdicts if current_verdict.flagged]
