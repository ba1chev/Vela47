from typing import Any

from tests.evals.evals_runners.evals_runner_base import EvalsRunnerBase
from tests.evals.evals_runners.evals_runners_type import EvalsRunnersType
from tests.evals.evals_runners.evals_runners_factory.evals_runners_registry import EVALS_RUNNERS_REGISTRY
from tests.evals.evals_runners.evals_runners_factory.evals_runners_factory_base import EvalsRunnersFactoryBase


class EvalsRunnersFactory(EvalsRunnersFactoryBase):
    """Concrete factory that maps each EvalsRunnersType to its EvalsRunnerBase subclass
    and delegates construction to it. Building a runner costs nothing — its containers
    and embeddings are prepared on its first run — so an eval module can create its
    runner when it is imported.

    Registry reference:
      DEEP_AGENT -> EvalsRunnerDeepAgent()
      RAG_AGENT  -> EvalsRunnerRagAgent()"""

    def create(self, type: EvalsRunnersType, **kwargs: Any) -> EvalsRunnerBase:
        cls = EVALS_RUNNERS_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No evals runner class registered for type '{type}'. "
                f"Known types: {list(EVALS_RUNNERS_REGISTRY)}"
            )

        return cls(**kwargs)
