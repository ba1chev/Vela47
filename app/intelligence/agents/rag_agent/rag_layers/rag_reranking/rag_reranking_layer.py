from pydantic import ValidationError

from app.intelligence.agents import RagContext
from app.intelligence.agents import RagRelevance
from app.intelligence.agents import RagLayerBase
from app.intelligence.agents import RagLayerType
from app.intelligence.model import ModelFoundation
from app.intelligence.messages import MessageHuman
from app.intelligence.messages import MessageSystem
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.memory import VectorDbOperationFilter
from app.intelligence.memory import VectorDbOperationRerank
from app.intelligence.outputs import OutputParserStructured
from app.intelligence.memory import VectorDbOperationManager
from app.intelligence.agents import RAG_RERANKING_SYSTEM_PROMPT


class RagRerankingLayer(RagLayerBase):
    """Keeps the candidates that actually answer the query, best first. One structured
    call scores every candidate from 0 to 10 against a schema from RagRelevance, passed
    as output_schema with exactly as many entries as passages: without the count, a
    model held to the schema answered with an empty list. Ordering and the cut are
    VectorDbOperationRerank and VectorDbOperationFilter, and sorting is stable.

    Passages are judged against the question as asked, with the rewrite shown only to
    resolve references. A reply that cannot be parsed keeps the candidates in
    retrieval order with relevance left empty, which is how the trace shows reranking
    was skipped."""

    PASSAGE_CHARS = 500

    def __init__(self, model: ModelFoundation, top_n: int = 4, min_score: int = 4) -> None:
        self._model: ModelFoundation = model
        self._top_n: int = top_n
        self._min_score: int = min_score
        self._parser: OutputParserStructured[RagRelevance] = OutputParserStructured(schema = RagRelevance)
        self._operation_manager: VectorDbOperationManager = VectorDbOperationManager()

    @property
    def layer_type(self) -> RagLayerType:
        return RagLayerType.RERANKING

    def _passage_text(self, entry: VectorDbMemoryEntry) -> str:
        content = entry.message.content if isinstance(entry.message.content, str) else str(entry.message.content)
        return content[:self.PASSAGE_CHARS]

    def _output_schema(self, count: int) -> dict:
        schema = RagRelevance.model_json_schema()
        schema["minItems"] = schema["maxItems"] = count
        return schema

    def _build_report(self, context: RagContext) -> str:
        goal = context.goal.content if isinstance(context.goal.content, str) else str(context.goal.content)
        lines = [f"QUERY: {goal}"]
        if context.query and context.query != goal:
            lines.append(f"SAME QUERY, WITH ITS REFERENCES RESOLVED: {context.query}")
        lines.extend(["", "PASSAGES:"])
        for number, current_entry in enumerate(context.candidates, start = 1):
            lines.append(f"[{number}] {self._passage_text(current_entry)}")
            lines.append("")
        return "\n".join(lines)

    def execute(self, context: RagContext) -> None:
        if not context.candidates:
            context.passages = []
            return

        response = self._model.invoke(
            [MessageSystem(content = RAG_RERANKING_SYSTEM_PROMPT), MessageHuman(content = self._build_report(context))],
            output_schema = self._output_schema(len(context.candidates))
        )

        try:
            relevance = self._parser.parse(response).data
        except ValidationError:
            context.passages = context.candidates[:self._top_n]
            return

        scores = {
            context.candidates[current_score.index - 1].message.id: current_score.score
            for current_score in relevance.root
            if 1 <= current_score.index <= len(context.candidates)
        }
        ranked = self._operation_manager.apply(
            [
                VectorDbOperationRerank(scorer = lambda entry: scores.get(entry.message.id, 0)),
                VectorDbOperationFilter(predicate = lambda entry: scores.get(entry.message.id, 0) >= self._min_score)
            ],
            context.candidates
        )
        context.relevance = scores
        context.passages = ranked[:self._top_n]
