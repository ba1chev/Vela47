from typing import Any, Optional

from app.intelligence.agents import RagContext
from app.intelligence.messages import MessageAI
from app.intelligence.agents import RagLayerBase
from app.intelligence.agents import RagLayerType
from app.intelligence.model import ModelFoundation
from app.intelligence.messages import MessageHuman
from app.intelligence.messages import MessageSystem
from app.intelligence.tracing import TraceEventType
from app.intelligence.tracing import TracingServiceNull
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.agents import RAG_NO_SOURCES_PROMPT
from app.intelligence.agents import RAG_GENERATION_SYSTEM_PROMPT


class RagGenerationLayer(RagLayerBase):
    """Writes the answer from the reranked passages and streams it as ANSWER_CHUNK
    events, like the DeepAgent's merging layer. Sources come first, each under its
    number and document title, and the question last, because what a small model reads
    last weighs most. The same numbers travel in response_metadata with document, chunk,
    section, score and excerpt, so a citation can be traced after the conversation is
    reopened.

    With no passage left the agent still answers, like a general assistant: a greeting
    or a question about the conversation from the conversation, anything else from the
    model's own knowledge, said to come from outside the documents and cited to
    nothing (see RAG_NO_SOURCES_PROMPT). Both answers are streamed the same way."""

    EXCERPT_CHARS = 240

    def __init__(self, model: ModelFoundation,
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        self._model: ModelFoundation = model
        self._tracing_service: TracingServiceBase = (
            tracing_service
            if tracing_service is not None
            else TracingServiceNull()
        )

    @property
    def layer_type(self) -> RagLayerType:
        return RagLayerType.GENERATION

    def _text_of(self, content: object) -> str:
        return content if isinstance(content, str) else str(content)

    def _build_prompt(self, context: RagContext) -> str:
        lines = ["SOURCES:"]
        for number, current_entry in enumerate(context.passages, start = 1):
            lines.append(f"[{number}] {current_entry.message.name}")
            lines.append(self._text_of(current_entry.message.content))
            lines.append("")
        lines.append(f"QUESTION: {self._text_of(context.goal.content)}")
        return "\n".join(lines)

    def _sources(self, context: RagContext) -> list[dict[str, Any]]:
        sources: list[dict[str, Any]] = []
        for number, current_entry in enumerate(context.passages, start = 1):
            metadata = current_entry.metadata
            sources.append({
                "index": number,
                "document_id": metadata.source.document_id if metadata is not None else None,
                "title": current_entry.message.name,
                "chunk_index": metadata.source.chunk_index if metadata is not None else None,
                "section": metadata.section if metadata is not None else None,
                "score": context.relevance.get(current_entry.message.id),
                "excerpt": self._text_of(current_entry.message.content)[:self.EXCERPT_CHARS]
            })
        return sources

    def _messages(self, context: RagContext) -> list:
        if not context.passages:
            return [
                MessageSystem(content = RAG_NO_SOURCES_PROMPT),
                *context.history,
                MessageHuman(content = self._text_of(context.goal.content))
            ]
        return [
            MessageSystem(content = RAG_GENERATION_SYSTEM_PROMPT),
            *context.history,
            MessageHuman(content = self._build_prompt(context))
        ]

    def execute(self, context: RagContext) -> None:
        messages = self._messages(context)
        parts: list[str] = []
        for current_chunk in self._model.stream(messages):
            parts.append(current_chunk)
            self._tracing_service.emit(
                TraceEventType.ANSWER_CHUNK, "answer", {"text": current_chunk}
            )

        context.final = MessageAI(
            content = "".join(parts),
            response_metadata = {"sources": self._sources(context)}
        )
