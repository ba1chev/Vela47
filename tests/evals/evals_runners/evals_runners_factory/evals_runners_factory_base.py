from typing import Any
from abc import ABC, abstractmethod

from tests.evals.evals_runners.evals_runner_base import EvalsRunnerBase
from tests.evals.evals_runners.evals_runners_type import EvalsRunnersType


class EvalsRunnersFactoryBase(ABC):
    """Abstract factory for EvalsRunnerBase instances. Lets an eval name the agent it
    runs by type, without importing the concrete runners and what they in turn import —
    the sandbox pool, the web fetcher, the indexer."""

    @abstractmethod
    def create(self, type: EvalsRunnersType, **kwargs: Any) -> EvalsRunnerBase:
        raise NotImplementedError("Must be implemented")
