import pytest
import asyncio

from app.intelligence.tracing import TraceEventType
from app.intelligence.tracing import TracingService
from app.intelligence.tracing import TracingServiceNull


def layer(service, label):
    return service.span(TraceEventType.LAYER_STARTED, TraceEventType.LAYER_FINISHED, label)


class TestTracingServiceTree:
    def test_started_and_finished_share_one_span_id(self):
        service = TracingService()
        with layer(service, "L"):
            pass
        started, finished = service.events()
        assert started.span_id == finished.span_id
        assert started.parent_id is None and finished.parent_id is None

    def test_events_inside_a_span_name_it_as_parent(self):
        service = TracingService()
        with layer(service, "outer"):
            service.emit(TraceEventType.MODEL_INVOKED, "m")
            with layer(service, "inner"):
                service.record("check", "auth")
        outer, model, inner, check, inner_done, outer_done = service.events()
        assert model.parent_id == outer.span_id and inner.parent_id == outer.span_id
        assert check.parent_id == inner.span_id
        assert inner_done.parent_id == outer.span_id and outer_done.parent_id is None

    def test_leaf_events_get_ids_of_their_own(self):
        service = TracingService()
        service.emit(TraceEventType.MODEL_INVOKED, "a")
        service.emit(TraceEventType.MODEL_INVOKED, "b")
        first, second = service.events()
        assert first.span_id != second.span_id

    def test_a_span_left_by_an_exception_finishes_as_an_error(self):
        service = TracingService()
        with pytest.raises(ValueError):
            with service.step("Read", "loader"):
                raise ValueError("bad bytes")
        finished = service.events()[-1]
        assert finished.type is TraceEventType.STEP_FINISHED
        assert finished.payload["status"] == "error"
        assert finished.payload["error"] == "ValueError: bad bytes"
        assert service.current_span_id() is None

    def test_step_and_record_carry_their_category(self):
        service = TracingService()
        with service.step("Chunk", "chunker", {"strategy": "recursive"}) as span:
            span["chunks"] = 3
        service.record("Quota", "quota", {"ok": True})
        started, finished, recorded = service.events()
        assert started.payload == {"category": "chunker", "strategy": "recursive"}
        assert finished.payload["chunks"] == 3
        assert recorded.type is TraceEventType.STEP_RECORDED and recorded.payload["category"] == "quota"

    def test_the_open_span_follows_work_into_a_thread(self):
        service = TracingService()

        async def run():
            with layer(service, "outer"):
                await asyncio.to_thread(service.record, "in thread", "db")

        asyncio.run(run())
        outer, recorded, _ = service.events()
        assert recorded.parent_id == outer.span_id

    def test_one_tracer_never_adopts_another_tracers_span(self):
        first, second = TracingService(), TracingService()
        with layer(first, "first"):
            second.record("elsewhere", "db")
        assert second.events()[0].parent_id is None

    def test_a_null_span_does_not_hide_the_real_parent(self):
        service = TracingService()
        with layer(service, "outer"):
            with layer(TracingServiceNull(), "ignored"):
                service.record("inside", "db")
        outer, recorded, _ = service.events()
        assert recorded.parent_id == outer.span_id
