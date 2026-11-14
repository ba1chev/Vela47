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
    score and excerpt, so a citation can be traced after the conversation is reopened.

    With no passage left, the model only tells the user the documents do not cover the
    question, which reaches it quoted inside that instruction: given anything that reads
    as a question, a small model answers from memory and cites a source it never had.
    That reply arrives whole rather than streamed."""

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
        return [
            {
                "index": number,
                "document_id": current_entry.message.additional_kwargs.get("document_id"),
                "title": current_entry.message.name,
                "chunk_index": current_entry.message.additional_kwargs.get("chunk_index"),
                "score": context.relevance.get(current_entry.message.id),
                "excerpt": self._text_of(current_entry.message.content)[:self.EXCERPT_CHARS]
            }
            for number, current_entry in enumerate(context.passages, start = 1)
        ]

    def _no_sources_reply(self, context: RagContext) -> str:
        response = self._model.invoke(
            [MessageHuman(content = RAG_NO_SOURCES_PROMPT.format(question = self._text_of(context.goal.content)))]
        )
        return self._text_of(response.content).strip()

    def execute(self, context: RagContext) -> None:
        if not context.passages:
            reply = self._no_sources_reply(context)
            self._tracing_service.emit(TraceEventType.ANSWER_CHUNK, "answer", {"text": reply})
            context.final = MessageAI(content = reply, response_metadata = {"sources": []})
            return

        messages = [
            MessageSystem(content = RAG_GENERATION_SYSTEM_PROMPT),
            *context.history,
            MessageHuman(content = self._build_prompt(context))
        ]
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
