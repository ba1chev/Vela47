from typing import Optional
from time import perf_counter

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
    inspect a text and reports every inspection to the run's tracer, timed, with the
    detector, where the text came from, the text itself and the whole verdict. A clean
    verdict is SECURITY_CHECKED and a flagged one SECURITY_FLAGGED, so findings can be
    counted on their own while the trace still shows everything that was checked. The
    text and the run go on unchanged.

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
        detector = self._detectors[threat]
        started = perf_counter()
        verdict = detector.inspect(text)
        self._tracing_service.emit(
            TraceEventType.SECURITY_FLAGGED if verdict.flagged else TraceEventType.SECURITY_CHECKED,
            f"{threat.value.capitalize()} in {source}" if verdict.flagged else f"{threat.value.capitalize()} check · {source}",
            {
                "source": source,
                "detector": type(detector).__name__,
                "text": text,
                **verdict.model_dump(mode = "json")
            },
            (perf_counter() - started) * 1000.0
        )
        return verdict
