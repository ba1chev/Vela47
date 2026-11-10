from typing import Any, Optional

from app.intelligence.tracing import TraceEventType
from app.intelligence.agents import OperationPolicy
from app.intelligence.agents import OperationContext
from app.intelligence.agents import OperationLayerBase
from app.intelligence.tracing import TracingServiceNull
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.agents import OperationLayersFactory
from app.intelligence.agents import OperationLayersFactoryBase


class OperationPipeline:
    """Runs the layers an OperationPolicy resolved, threading one OperationContext
    through them. It is deliberately the dumbest component: it knows nothing of what a
    layer does and never branches, so adding a stage never touches it. Layers are
    resolved once, at construction.

    It is also the only place that times layers, and it reports what each produced by
    reading the context afterwards, so layers need no tracer of their own. Only work the
    context cannot describe, such as one subagent's run, is reported by the layer
    itself."""

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
        return {
            "steps": len(context.plan.steps) if context.plan is not None else 0,
            "tasks": len(context.tasks),
            "results": len(context.results),
            "has_final": context.final is not None
        }

    def run(self, context: OperationContext) -> OperationContext:
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
