from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageHuman
from app.intelligence.security import SecurityMonitor
from tests.fixtures.agents.echo_agent import EchoAgent
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.security import SecurityPromptType


class FlaggingEchoAgent(EchoAgent):
    """An EchoAgent whose run has a text inspected for injection through a
    SecurityMonitor on its tracer before it answers, as a page read by a tool would be.
    Lets a stream test check what happens to a finding: where it is logged and whether
    it stays with the stored answer."""

    def __init__(self, tracing_service: TracingServiceBase, text: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._security_monitor: SecurityMonitor = SecurityMonitor(tracing_service)
        self._text: str = text

    def execute(self, human_message: MessageHuman) -> MessageAI:
        self._security_monitor.inspect(SecurityPromptType.INJECTION, self._text, "fetch_url")
        return super().execute(human_message)
