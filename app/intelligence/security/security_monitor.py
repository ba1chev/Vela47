from typing import Optional

from app.intelligence.security import SecurityType
from app.intelligence.security import SecurityBase
from app.intelligence.tracing import TraceEventType
from app.intelligence.security import SecurityFactory
from app.intelligence.security import SecurityVerdict
from app.intelligence.tracing import TracingServiceNull
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.security import SecurityPromptType
from app.intelligence.security import SecurityFactoryBase


class SecurityMonitor:
    """The monitor mode of the security layer: it has the detector of a prompt threat
    inspect a text and reports a flagged verdict to the run's tracer as SECURITY_FLAGGED,
    with where the text came from. The text and the run go on unchanged, and a clean
    verdict leaves no event, so only what was found shows in the trace.

    One per run, like the tracer it reports to. The detectors of every prompt threat are
    built once, through the factory, when the monitor is."""

    def __init__(self, tracing_service: Optional[TracingServiceBase] = None,
        security_factory: Optional[SecurityFactoryBase] = None) -> None:
        factory = security_factory if security_factory is not None else SecurityFactory()
        self._detectors: dict[SecurityPromptType, SecurityBase] = {
            current_type: factory.create(SecurityType.PROMPT, current_type) for current_type in SecurityPromptType
        }
        self._tracing_service: TracingServiceBase = (
            tracing_service
            if tracing_service is not None
            else TracingServiceNull()
        )

    def inspect(self, threat: SecurityPromptType, text: str, source: str) -> SecurityVerdict:
        verdict = self._detectors[threat].inspect(text)
        if verdict.flagged:
            self._tracing_service.emit(
                TraceEventType.SECURITY_FLAGGED,
                f"{threat.value.capitalize()} in {source}",
                {"source": source, **verdict.model_dump(mode = "json")}
            )
        return verdict
