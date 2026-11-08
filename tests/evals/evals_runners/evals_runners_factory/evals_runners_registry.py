from tests.evals.evals_runners.evals_runner_base import EvalsRunnerBase
from tests.evals.evals_runners.evals_runners_type import EvalsRunnersType
from tests.evals.evals_runners.evals_runner_rag_agent import EvalsRunnerRagAgent
from tests.evals.evals_runners.evals_runner_deep_agent import EvalsRunnerDeepAgent


EVALS_RUNNERS_REGISTRY: dict[EvalsRunnersType, type[EvalsRunnerBase]] = {
    EvalsRunnersType.DEEP_AGENT: EvalsRunnerDeepAgent,
    EvalsRunnersType.RAG_AGENT: EvalsRunnerRagAgent
}
