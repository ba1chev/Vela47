from app.intelligence.model import ModelEmbeddings
from app.intelligence.tracing import TraceEventType
from app.intelligence.tracing import TracingService
from app.intelligence.tracing import TracingServiceNull
from app.intelligence.tracing import current_tracing_service
from tests.fixtures.model.scripted_model_client import ScriptedModelClient


class TestTracingContext:
    def test_outside_any_span_there_is_a_tracer_that_discards_everything(self):
        tracer = current_tracing_service()
        assert isinstance(tracer, TracingServiceNull) and tracer.events() == []

    def test_inside_a_span_it_is_the_tracer_of_that_span(self):
        service = TracingService()
        with service.step("Upload", "ingest"):
            assert current_tracing_service() is service
        assert current_tracing_service() is not service

    def test_a_shared_component_reports_to_the_run_that_uses_it(self):
        service = TracingService()
        embeddings = ModelEmbeddings("embedder", client = ScriptedModelClient())
        with service.step("Chunking", "chunker"):
            embeddings.embed_many(["one", "two"])
        started, invoked, _ = service.events()
        assert invoked.type is TraceEventType.MODEL_INVOKED and invoked.parent_id == started.span_id

    def test_a_component_given_a_tracer_keeps_reporting_to_it(self):
        own, other = TracingService(), TracingService()
        embeddings = ModelEmbeddings("embedder", own, client = ScriptedModelClient())
        with other.step("Elsewhere", "chunker"):
            embeddings.embed("one")
        assert [current.type for current in own.events()] == [TraceEventType.MODEL_INVOKED]
        assert len(other.events()) == 2
