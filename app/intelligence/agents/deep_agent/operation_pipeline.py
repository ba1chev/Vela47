from typing import Any, Optional

from app.intelligence.tracing.trace_event_type import TraceEventType
from app.intelligence.tracing.tracing_service_null import TracingServiceNull
from app.intelligence.tracing.tracing_service_base import TracingServiceBase
from app.intelligence.agents.deep_agent.operation_context import OperationContext
from app.intelligence.agents.deep_agent.operation_policies.operation_policy import OperationPolicy
from app.intelligence.agents.deep_agent.operation_layers.operation_layer_base import OperationLayerBase
from app.intelligence.agents.deep_agent.operation_layers.operation_layers_factory.operation_layers_factory import OperationLayersFactory
from app.intelligence.agents.deep_agent.operation_layers.operation_layers_factory.operation_layers_factory_base import OperationLayersFactoryBase


class OperationPipeline:
    """Executes the layer sequence an OperationPolicy resolved, threading one
    OperationContext through all of them.

    The pipeline is intentionally the dumbest component here: it holds no
    knowledge of what any layer does, does not branch, and does not inspect the
    context between stages. Everything variable — which stages run, in what
    order, with which dependencies — is decided by the policy at construction
    time. Adding a stage therefore never touches this class.

    It is also the only place that times layers. Because every layer writes its
    result into the shared context, the pipeline can report what a layer produced
    by reading the context afterwards, which means layers need no tracer of their
    own to be visible in the UI. Only work the context cannot describe — an
    individual subagent running inside a stage — is reported by the layer itself.

    Layers are resolved once in the constructor rather than per run, so a
    pipeline is a reusable, immutable plan of execution."""

    def __init__(self, operation_policy: OperationPolicy,
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        self._operation_policy: OperationPolicy = operation_policy
        self._tracing_service: TracingServiceBase = (
            tracing_service
            if tracing_service is not None
            else TracingServiceNull()
        )
        operation_layers_factory: OperationLayersFactoryBase = OperationLayersFactory()
        self._operation_layers: list[OperationLayerBase] = operation_policy.resolve(
            operation_layers_factory
        )

    def _summarize(self, context: OperationContext) -> dict[str, Any]:
        """Describes the run's current state from the context alone. This is what a
        layer contributes to the UI without having to report anything itself."""
        return {
            "steps": len(context.plan.steps) if context.plan is not None else 0,
            "tasks": len(context.tasks),
            "results": len(context.results),
            "has_final": context.final is not None
        }

    def run(self, context: OperationContext) -> OperationContext:
        """Returns the same context instance it was given, now filled in by every
        layer. Returning the whole context rather than just context.final is what
        lets a caller inspect the plan and the individual subagent results for
        tracing, not only the merged answer."""
        with self._tracing_service.span(
            TraceEventType.PIPELINE_STARTED,
            TraceEventType.PIPELINE_FINISHED,
            "Pipeline",
            {"layers": len(self._operation_layers)}
        ) as pipeline_span:
            for current_layer in self._operation_layers:
                with self._tracing_service.span(
                    TraceEventType.LAYER_STARTED,
                    TraceEventType.LAYER_FINISHED,
                    current_layer.operation_type.name.title()
                ) as layer_span:
                    current_layer.execute(context)
                    layer_span.update(self._summarize(context))
            pipeline_span.update(self._summarize(context))
        return context

    def __len__(self) -> int:
        return len(self._operation_layers)
