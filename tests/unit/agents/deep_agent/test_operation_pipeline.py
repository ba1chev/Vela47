from app.intelligence.agents import OperationType
from app.intelligence.messages import MessageHuman
from app.intelligence.tracing import TracingService
from app.intelligence.tracing import TraceEventType
from app.intelligence.agents import OperationContext
from app.intelligence.agents import OperationPipeline
from tests.fixtures.agents.static_policy import StaticPolicy
from tests.fixtures.agents.recording_layer import RecordingLayer


def make_pipeline(log, tracer = None):
    layers = [
        RecordingLayer(OperationType.PLANNING, log, "planning"),
        RecordingLayer(OperationType.DECOMPOSITION, log, "decomposition"),
        RecordingLayer(OperationType.MERGING, log, "merging"),
    ]
    return OperationPipeline(StaticPolicy(layers), tracer)


class TestOperationPipeline:
    def test_layers_are_resolved_once_at_construction(self):
        assert len(make_pipeline([])) == 3

    def test_layers_run_in_the_order_the_policy_gave(self):
        log = []
        make_pipeline(log).run(OperationContext(goal = MessageHuman(content = "x")))
        assert log == ["planning", "decomposition", "merging"]

    def test_the_same_context_instance_is_returned(self):
        """Callers inspect the plan and the individual results, not only the answer."""
        context = OperationContext(goal = MessageHuman(content = "x"))
        assert make_pipeline([]).run(context) is context

    def test_a_pipeline_can_be_run_more_than_once(self):
        log = []
        pipeline = make_pipeline(log)
        pipeline.run(OperationContext(goal = MessageHuman(content = "a")))
        pipeline.run(OperationContext(goal = MessageHuman(content = "b")))
        assert len(log) == 6

    def test_without_a_tracer_it_still_runs(self):
        log = []
        make_pipeline(log).run(OperationContext(goal = MessageHuman(content = "x")))
        assert log

    def test_it_reports_a_span_for_every_layer(self):
        tracer = TracingService()
        make_pipeline([], tracer).run(OperationContext(goal = MessageHuman(content = "x")))
        started = [e for e in tracer.events() if e.type is TraceEventType.LAYER_STARTED]
        finished = [e for e in tracer.events() if e.type is TraceEventType.LAYER_FINISHED]
        assert len(started) == 3 and len(finished) == 3

    def test_it_brackets_the_run_with_pipeline_events(self):
        tracer = TracingService()
        make_pipeline([], tracer).run(OperationContext(goal = MessageHuman(content = "x")))
        events = tracer.events()
        assert events[0].type is TraceEventType.PIPELINE_STARTED
        assert events[-1].type is TraceEventType.PIPELINE_FINISHED

    def test_layer_names_reach_the_trace(self):
        tracer = TracingService()
        make_pipeline([], tracer).run(OperationContext(goal = MessageHuman(content = "x")))
        labels = [e.label for e in tracer.events() if e.type is TraceEventType.LAYER_STARTED]
        assert labels == ["Planning", "Decomposition", "Merging"]

    def test_finished_layers_carry_a_duration(self):
        tracer = TracingService()
        make_pipeline([], tracer).run(OperationContext(goal = MessageHuman(content = "x")))
        finished = [e for e in tracer.events() if e.type is TraceEventType.LAYER_FINISHED]
        assert all(e.duration_ms is not None for e in finished)
