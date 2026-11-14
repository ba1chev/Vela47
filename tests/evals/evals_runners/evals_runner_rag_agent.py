import re
import time

from app.intelligence.messages import MessageAI
from app.server.builders import build_rag_agent
from app.server.builders import build_rag_indexer
from app.intelligence.messages import MessageHuman
from app.intelligence.tracing import TracingService
from app.intelligence.memory import VectorDbMemoryEntry
from app.server.config_environment import ConfigEnvironment
from tests.evals.evals_runners.evals_runner_base import EvalsRunnerBase
from tests.evals.evals_runners.evals_runners_type import EvalsRunnersType
from tests.evals.evals_cases.evals_case_rag_agent import EvalsCaseRagAgent
from tests.evals.evals_runners.evals_record_rag_agent import EvalsRecordRagAgent
from tests.evals.evals_cases.evals_cases_rag_agent import EVALS_DOCUMENTS_RAG_AGENT


class EvalsRunnerRagAgent(EvalsRunnerBase[EvalsCaseRagAgent, EvalsRecordRagAgent]):
    """Runs the real RAG agent — the server's builder, the local models and the same
    indexer uploads go through — on an eval case over EVALS_DOCUMENTS_RAG_AGENT.

    start() chunks and embeds the documents once; every run then builds a fresh agent
    over those entries, as the server does for each request, and restores the case's
    earlier turns into it before the question is asked.

    The language check tells Cyrillic from Latin script, which is all the cases need:
    a Bulgarian answer must be mostly Cyrillic, any other almost none."""

    CITATION = re.compile(r"\[\d+\]")

    def __init__(self) -> None:
        super().__init__()
        self._entries: list[VectorDbMemoryEntry] = []

    @property
    def runner_type(self) -> EvalsRunnersType:
        return EvalsRunnersType.RAG_AGENT

    def start(self) -> None:
        self._require_ollama()
        indexer = build_rag_indexer(ConfigEnvironment.DEV)
        self._entries = []
        for number, (title, text) in enumerate(EVALS_DOCUMENTS_RAG_AGENT.items()):
            self._entries.extend(indexer.index(f"eval-{number}", title, text))

    def _cyrillic_share(self, text: str) -> float:
        letters = [current for current in text if current.isalpha()]
        return sum("Ѐ" <= current <= "ӿ" for current in letters) / len(letters) if letters else 0.0

    def run(self, case: EvalsCaseRagAgent, run: int) -> EvalsRecordRagAgent:
        agent = build_rag_agent(TracingService(), self._entries, ConfigEnvironment.DEV)
        history = []
        for asked, answered in case.history:
            history.extend([MessageHuman(content = asked), MessageAI(content = answered, name = "rag")])
        agent.restore(history)

        started = time.monotonic()
        try:
            reply = agent.execute(MessageHuman(content = case.question))
            answer, sources, crashed = reply.content, reply.response_metadata.get("sources", []), None
        except Exception as error:
            answer, sources, crashed = "", [], f"{type(error).__name__}: {str(error)[:300]}"
        elapsed = time.monotonic() - started

        cyrillic = self._cyrillic_share(answer)
        return EvalsRecordRagAgent(
            case = case.id,
            run = run,
            elapsed = round(elapsed, 1),
            crashed = crashed,
            answer = answer,
            sources = len(sources),
            facts_found = crashed is None and all(re.search(current, answer, re.IGNORECASE) for current in case.facts),
            cites = bool(self.CITATION.search(answer)),
            language_ok = crashed is None and (cyrillic > 0.5 if case.language == "bg" else cyrillic < 0.1),
            reranked = all(current.get("score") is not None for current in sources) if sources else None
        )
