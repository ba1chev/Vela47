from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageHuman
from app.intelligence.tracing import TraceEventType
from tests.fixtures.agents.echo_agent import EchoAgent
from app.intelligence.tracing import TracingServiceBase


class TracingEchoAgent(EchoAgent):
    """An EchoAgent that reports a short run to its tracer before it answers: a
    pipeline around one model call and one tool call with a long result, a sandbox
    lease and an answer chunk. Lets a stream test check which events are kept with
    the stored answer and how long their texts may be."""

    def __init__(self, tracing_service: TracingServiceBase, tool_result: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tracing_service: TracingServiceBase = tracing_service
        self._tool_result: str = tool_result

    def execute(self, human_message: MessageHuman) -> MessageAI:
        self._tracing_service.emit(TraceEventType.PIPELINE_STARTED, "Pipeline")
        self._tracing_service.emit(TraceEventType.SANDBOX_ACQUIRED, "slot 0")
        self._tracing_service.emit(TraceEventType.MODEL_INVOKED, "qwen3:1.7b", {"total_tokens": 42})
        self._tracing_service.emit(TraceEventType.TOOL_EXECUTED, "fetch_url", {"result": self._tool_result})
        self._tracing_service.emit(TraceEventType.ANSWER_CHUNK, "chunk", {"text": "Echo"})
        self._tracing_service.emit(TraceEventType.SANDBOX_RELEASED, "slot 0")
        self._tracing_service.emit(TraceEventType.PIPELINE_FINISHED, "Pipeline", duration_ms = 12.5)
        return super().execute(human_message)
