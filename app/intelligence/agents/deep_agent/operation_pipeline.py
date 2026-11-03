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
