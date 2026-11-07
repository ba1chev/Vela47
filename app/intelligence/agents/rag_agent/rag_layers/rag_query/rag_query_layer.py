from app.intelligence.agents import RagContext
from app.intelligence.agents import RagLayerBase
from app.intelligence.agents import RagLayerType
from app.intelligence.messages import MessageType
from app.intelligence.messages import MessageHuman
from app.intelligence.model import ModelFoundation
from app.intelligence.messages import MessageSystem
from app.intelligence.agents import RAG_QUERY_SYSTEM_PROMPT


class RagQueryLayer(RagLayerBase):
    """Makes the question searchable on its own. A follow-up such as 'and what does it
    cost?' contains nothing a search could match — the 'it' lives in an earlier turn —
    so with history present the model rewrites the question into a standalone query.

    Without history there is nothing to resolve and no model call is made: the question
    is already the query. That keeps the first question of every conversation one model
    call cheaper, and keeps the rewrite from ever drifting away from what was asked.

    The history reaches the model as a transcript inside one message, not as chat turns.
    Handed real turns, a small model does what turns invite — it continues the
    conversation and answers the question. And a reply far longer than the question is
    taken for exactly that and discarded, so a stray answer never becomes the search."""

    TURN_CHARS = 400
    MAX_EXTRA_CHARS = 160

    def __init__(self, model: ModelFoundation) -> None:
        self._model: ModelFoundation = model

    @property
    def layer_type(self) -> RagLayerType:
        return RagLayerType.QUERY

    def _text_of(self, content: object) -> str:
        return content if isinstance(content, str) else str(content)

    def _build_transcript(self, context: RagContext) -> str:
        speakers = {MessageType.HUMAN_MESSAGE: "User", MessageType.AI_MESSAGE: "Assistant"}
        lines = ["CONVERSATION:"]
        lines.extend(
            f"{speakers[current_message.type]}: {self._text_of(current_message.content)[:self.TURN_CHARS]}"
            for current_message in context.history
            if current_message.type in speakers
        )
        lines.extend(["", f"LATEST MESSAGE: {self._text_of(context.goal.content)}", "", "STANDALONE QUERY:"])
        return "\n".join(lines)

    def execute(self, context: RagContext) -> None:
        goal = self._text_of(context.goal.content)

        if not context.history:
            context.query = goal
            return

        response = self._model.invoke([
            MessageSystem(content = RAG_QUERY_SYSTEM_PROMPT),
            MessageHuman(content = self._build_transcript(context))
        ])
        lines = [
            current_line.strip().strip("\"'/").strip()
            for current_line in self._text_of(response.content).splitlines()
            if current_line.strip()
        ]
        rewritten = lines[0] if lines else ""
        context.query = rewritten if 0 < len(rewritten) <= len(goal) + self.MAX_EXTRA_CHARS else goal
