from app.intelligence.tracing import TraceEventType
from app.intelligence.tracing import TracingService


class TestTracingService:
    def test_starts_with_no_events(self):
        assert TracingService().events() == []

    def test_emit_records_event(self):
        service = TracingService()
        service.emit(TraceEventType.MODEL_INVOKED, "qwen3")
        events = service.events()
        assert len(events) == 1
        assert events[0].type == TraceEventType.MODEL_INVOKED
        assert events[0].label == "qwen3"

    def test_payload_preserved(self):
        service = TracingService()
        service.emit(TraceEventType.TOOL_EXECUTED, "add", {"status": "success"})
        assert service.events()[0].payload == {"status": "success"}

    def test_events_returns_a_copy(self):
        service = TracingService()
        service.emit(TraceEventType.MODEL_INVOKED, "a")
        service.events().clear()
        assert len(service.events()) == 1

    def test_empty_service_is_truthy(self):
        assert bool(TracingService())

    def test_subscriber_receives_events(self):
        service = TracingService()
        seen = []
        service.subscribe(seen.append)
        service.emit(TraceEventType.LAYER_STARTED, "Planning")
        assert len(seen) == 1
        assert seen[0].label == "Planning"

    def test_subscriber_does_not_receive_earlier_events(self):
        service = TracingService()
        service.emit(TraceEventType.LAYER_STARTED, "before")
        seen = []
        service.subscribe(seen.append)
        service.emit(TraceEventType.LAYER_FINISHED, "after")
        assert [event.label for event in seen] == ["after"]

    def test_ordering_is_preserved(self):
        service = TracingService()
        for index in range(5):
            service.emit(TraceEventType.MODEL_INVOKED, str(index))
        assert [event.label for event in service.events()] == ["0", "1", "2", "3", "4"]
