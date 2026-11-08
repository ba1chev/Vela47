import sys
import json
import ollama
import pathlib
import statistics
from typing import Callable

from tests.evals.evals_settings import EVALS_JUDGE_MODEL
from tests.evals.evals_runners.evals_record_base import EvalsRecordBase
from tests.evals.evals_runners.evals_runners_type import EvalsRunnersType
from tests.evals.evals_cases.evals_cases_rag_agent import EVALS_CASES_RAG_AGENT
from tests.evals.evals_runners.evals_record_rag_agent import EvalsRecordRagAgent
from tests.evals.evals_cases.evals_cases_deep_agent import EVALS_CASES_DEEP_AGENT
from tests.evals.evals_runners.evals_record_deep_agent import EvalsRecordDeepAgent
from tests.evals.evals_cases.evals_cases_rag_agent import EVALS_DOCUMENTS_RAG_AGENT


class EvalsJudge:
    """Scores the answers of an eval session from 1 to 5 for helpfulness and
    faithfulness, with a larger local model than the one being evaluated.

    It runs on its own, after the evals and over their results directory:
        .venv/bin/python -m tests.evals.evals_judge tests/evals/results/<session>
    rather than inside them, for two reasons. Its scores are opinions — the same answer
    can get a 3 or a 5 — so they inform a comparison but must never fail a test. And
    the judge model is large: loaded beside the agents' model it pushes a 24 GB machine
    into swap, so it is loaded once, when the agents are done. Unload it afterwards with
    `ollama stop qwen3:14b`.

    A deep agent answer is judged against the reports its subagents wrote, a RAG answer
    against the documents themselves. The judge is told to judge only against that
    evidence, but it still knows what it was trained on — a fact newer than its
    training, such as a recent release, can be marked unfaithful when it is not. Read
    the reasons in <runner type>_judged.jsonl before trusting a drop in faithfulness."""

    SCHEMA = {
        "type": "object",
        "properties": {
            "helpfulness": {"type": "integer", "minimum": 1, "maximum": 5},
            "faithfulness": {"type": "integer", "minimum": 1, "maximum": 5},
            "reason": {"type": "string"}
        },
        "required": ["helpfulness", "faithfulness", "reason"]
    }
    PROMPT = """You grade the final answer an AI assistant gave to a user. You get the user's request, the evidence the assistant had, and the answer.

Score from 1 (very poor) to 5 (excellent):
- helpfulness: does the answer directly and usefully address what the user asked, at a sensible length? When the evidence does not hold the answer, the most helpful answer says so clearly and briefly.
- faithfulness: is every concrete claim in the answer supported by the evidence? Penalise invented facts, numbers, versions or results, and anything taken from general knowledge instead of the evidence.

Judge only against the evidence given. Be strict and consistent. Reply with JSON only."""

    def __init__(self, model: str = EVALS_JUDGE_MODEL) -> None:
        self._model: str = model
        self._judges: dict[EvalsRunnersType, tuple[type[EvalsRecordBase], Callable[[EvalsRecordBase], dict]]] = {
            EvalsRunnersType.DEEP_AGENT: (EvalsRecordDeepAgent, self._deep_agent),
            EvalsRunnersType.RAG_AGENT: (EvalsRecordRagAgent, self._rag_agent)
        }

    def _score(self, request: str, evidence: str, answer: str) -> dict:
        reply = ollama.chat(
            model = self._model,
            messages = [
                {"role": "system", "content": self.PROMPT},
                {"role": "user", "content": f"USER REQUEST:\n{request}\n\nEVIDENCE:\n{evidence or '(none)'}\n\nANSWER:\n{answer[:4000]}"}
            ],
            options = {"temperature": 0, "num_ctx": 8192},
            think = False,
            format = self.SCHEMA
        )
        return json.loads(reply["message"]["content"])

    def _deep_agent(self, record: EvalsRecordDeepAgent) -> dict:
        case = next(current for current in EVALS_CASES_DEEP_AGENT if current.id == record.case)
        evidence = "\n\n".join(f"[{current['status']}] {current['result'][:1500]}" for current in record.reports)
        return self._score(case.goal, evidence[:6000], record.final)

    def _rag_agent(self, record: EvalsRecordRagAgent) -> dict:
        case = next(current for current in EVALS_CASES_RAG_AGENT if current.id == record.case)
        documents = "\n\n".join(f"=== {title} ===\n{text}" for title, text in EVALS_DOCUMENTS_RAG_AGENT.items())
        history = "".join(f"User: {asked}\nAssistant: {answered}\n" for asked, answered in case.history)
        return self._score(f"{history}User: {case.question}" if history else case.question, documents, record.answer)

    def judge(self, directory: pathlib.Path) -> list[str]:
        lines = []
        for runner_type, (record_class, score) in self._judges.items():
            path = directory / f"{runner_type.value}.jsonl"
            if not path.exists():
                continue

            records = [record_class.model_validate_json(current) for current in path.read_text(encoding = "utf-8").splitlines() if current]
            verdicts = [
                {"helpfulness": 1, "faithfulness": 1, "reason": "the run crashed"} if current.crashed else score(current)
                for current in records
            ]
            (directory / f"{runner_type.value}_judged.jsonl").write_text(
                "".join(
                    json.dumps({**current.model_dump(), "judge": verdict}, ensure_ascii = False) + "\n"
                    for current, verdict in zip(records, verdicts)
                ),
                encoding = "utf-8"
            )
            for case_id in dict.fromkeys(current.case for current in records):
                scored = [verdict for current, verdict in zip(records, verdicts) if current.case == case_id]
                lines.append(
                    f"{runner_type.value:10s} {case_id:26s} judge "
                    f"helpfulness={round(statistics.mean(current['helpfulness'] for current in scored), 2)} "
                    f"faithfulness={round(statistics.mean(current['faithfulness'] for current in scored), 2)}"
                )

        with (directory / "summary.txt").open("a", encoding = "utf-8") as output:
            output.write("".join(current + "\n" for current in lines))
        return lines


if __name__ == "__main__":
    for current_line in EvalsJudge().judge(pathlib.Path(sys.argv[1])):
        print(current_line)
