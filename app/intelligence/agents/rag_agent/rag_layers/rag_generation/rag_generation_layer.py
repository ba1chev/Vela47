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
    """Writes the answer from the reranked passages and streams it as it is produced,
    reporting every chunk as an ANSWER_CHUNK event exactly as the DeepAgent's merging
    layer does, so the browser renders both agents' answers the same way.

    Sources are numbered in the order reranking left them, and the same numbers travel
    with the answer in response_metadata — document, chunk, score and an excerpt — so a
    citation such as [2] can always be traced back to the passage it came from, even
    after the conversation is stored and reopened.

    When no passage survived, the model gets a different, narrower task: tell the user
    the documents do not cover the question, and nothing else. The question reaches it
    only quoted inside that instruction — never as a message of its own, nor beside an
    empty list of sources — because handed anything that reads as a question to
    answer, a small model answers it from what it happens to know and cites a source
    it was never given, which reads exactly like a grounded answer."""

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
        lines = [f"QUESTION: {self._text_of(context.goal.content)}", "", "SOURCES:"]
        for number, current_entry in enumerate(context.passages, start = 1):
            lines.append(f"[{number}] ({current_entry.message.name}) {self._text_of(current_entry.message.content)}")
            lines.append("")
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

    def execute(self, context: RagContext) -> None:
        messages = (
            [
                MessageSystem(content = RAG_GENERATION_SYSTEM_PROMPT),
                *context.history,
                MessageHuman(content = self._build_prompt(context))
            ]
            if context.passages
            else [MessageHuman(content = RAG_NO_SOURCES_PROMPT.format(
                question = self._text_of(context.goal.content)
            ))]
        )

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
