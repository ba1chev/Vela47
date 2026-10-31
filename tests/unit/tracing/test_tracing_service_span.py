import pytest

from app.intelligence.tracing import TraceEventType
from app.intelligence.tracing import TracingService


class TestTracingServiceSpan:
    def test_span_emits_started_and_finished(self):
        service = TracingService()
        with service.span(TraceEventType.LAYER_STARTED, TraceEventType.LAYER_FINISHED, "L"):
            pass
        assert [event.type for event in service.events()] == [
            TraceEventType.LAYER_STARTED,
            TraceEventType.LAYER_FINISHED
        ]

    def test_span_times_the_block(self):
        service = TracingService()
        with service.span(TraceEventType.LAYER_STARTED, TraceEventType.LAYER_FINISHED, "L"):
            pass
        assert service.events()[1].duration_ms is not None
        assert service.events()[0].duration_ms is None

    def test_span_body_contributes_to_finished_payload(self):
        service = TracingService()
        with service.span(
            TraceEventType.SUBAGENT_STARTED, TraceEventType.SUBAGENT_FINISHED,
            "RESEARCH", {"task_id": "t1"}
        ) as span:
            span["status"] = "success"
        finished = service.events()[1]
        assert finished.payload == {"task_id": "t1", "status": "success"}

    def test_span_closes_when_body_raises(self):
        service = TracingService()
        with pytest.raises(ValueError):
            with service.span(TraceEventType.LAYER_STARTED, TraceEventType.LAYER_FINISHED, "L"):
                raise ValueError("boom")
        assert service.events()[-1].type == TraceEventType.LAYER_FINISHED

    def test_started_payload_not_polluted_by_body(self):
        service = TracingService()
        with service.span(
            TraceEventType.LAYER_STARTED, TraceEventType.LAYER_FINISHED, "L", {"a": 1}
        ) as span:
            span["b"] = 2
        assert service.events()[0].payload == {"a": 1}
