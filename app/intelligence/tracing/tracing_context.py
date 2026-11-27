from app.intelligence.tracing import CURRENT_SPAN
from app.intelligence.tracing import TracingServiceNull
from app.intelligence.tracing import TracingServiceBase

NULL_TRACING_SERVICE = TracingServiceNull()


def current_tracing_service() -> TracingServiceBase:
    current = CURRENT_SPAN.get()
    return current[0] if current is not None else NULL_TRACING_SERVICE
