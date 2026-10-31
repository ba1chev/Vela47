from app.intelligence.tracing import TraceEventType
from app.intelligence.tracing import TracingServiceNull


class TestTracingServiceNull:
    def test_emit_records_nothing(self):
        service = TracingServiceNull()
        service.emit(TraceEventType.MODEL_INVOKED, "x")
        assert service.events() == []

    def test_subscriber_is_never_called(self):
        service = TracingServiceNull()
        seen = []
        service.subscribe(seen.append)
        service.emit(TraceEventType.MODEL_INVOKED, "x")
        assert seen == []

    def test_span_is_usable(self):
        service = TracingServiceNull()
        with service.span(TraceEventType.LAYER_STARTED, TraceEventType.LAYER_FINISHED, "L") as span:
            span["status"] = "success"
        assert service.events() == []

    def test_is_truthy(self):
        assert bool(TracingServiceNull())
