from typing import Any, Optional

from app.intelligence.agents import RagPolicy
from app.intelligence.agents import RagContext
from app.intelligence.agents import RagLayerBase
from app.intelligence.tracing import TraceEventType
from app.intelligence.agents import RagLayersFactory
from app.intelligence.tracing import TracingServiceNull
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.agents import RagLayersFactoryBase


class RagPipeline:
    """Executes the layer sequence a RagPolicy resolved, threading one RagContext
    through all of them — built the same way as OperationPipeline and reporting the same
    events. A run opens a pipeline span, every layer runs inside a layer span labelled
    with its type, and the trace panel renders the RAG agent's stages with no code of
    its own.

    What a layer produced is read off the context afterwards — the rewritten query, how
    many candidates retrieval found, how many passages reranking kept, whether reranking
    actually scored them — so no layer needs a tracer to be visible.

    Layers are resolved once in the constructor, so a pipeline is a reusable plan of
    execution."""

    def __init__(self, rag_policy: RagPolicy,
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        self._rag_policy: RagPolicy = rag_policy
        self._tracing_service: TracingServiceBase = (
            tracing_service
            if tracing_service is not None
            else TracingServiceNull()
        )
        rag_layers_factory: RagLayersFactoryBase = RagLayersFactory()
        self._rag_layers: list[RagLayerBase] = rag_policy.resolve(rag_layers_factory)

    def _summarize(self, context: RagContext) -> dict[str, Any]:
        return {
            "query": context.query,
            "candidates": len(context.candidates),
            "passages": len(context.passages),
            "reranked": bool(context.relevance),
            "has_final": context.final is not None
        }

    def run(self, context: RagContext) -> RagContext:
        with self._tracing_service.span(
            TraceEventType.PIPELINE_STARTED,
            TraceEventType.PIPELINE_FINISHED,
            "Pipeline",
            {"layers": len(self._rag_layers), "agent": "rag"}
        ) as pipeline_span:
            for current_layer in self._rag_layers:
                with self._tracing_service.span(
                    TraceEventType.LAYER_STARTED,
                    TraceEventType.LAYER_FINISHED,
                    current_layer.layer_type.name.title()
                ) as layer_span:
                    current_layer.execute(context)
                    layer_span.update(self._summarize(context))
            pipeline_span.update(self._summarize(context))
        return context

    def __len__(self) -> int:
        return len(self._rag_layers)
