from typing import Optional

from app.intelligence.sandbox import SandboxPoolBase
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.model import ModelFoundation
from app.intelligence.agents import OperationPolicy
from app.intelligence.agents import OperationType
from app.intelligence.agents import OperationLayerBase
from app.intelligence.agents import OperationLayersFactoryBase
from app.intelligence.agents import OperationSubagentFactoryBase


class OperationPolicyFull(OperationPolicy):
    """Runs the complete pipeline — plan, decompose, execute, merge.

    The planning and merging models are separate parameters because the two jobs
    reward opposite settings: planning wants low temperature and reasoning mode
    to produce a schema-valid breakdown, merging wants a model good at prose.
    Passing the same instance twice is fine when that distinction does not
    matter."""

    def __init__(self, planning_model: ModelFoundation, merging_model: ModelFoundation,
        subagent_factory: OperationSubagentFactoryBase,
        sandbox_pool: SandboxPoolBase,
        tracing_service: Optional[TracingServiceBase] = None) -> None:
        self._planning_model: ModelFoundation = planning_model
        self._merging_model: ModelFoundation = merging_model
        self._subagent_factory: OperationSubagentFactoryBase = subagent_factory
        self._sandbox_pool: SandboxPoolBase = sandbox_pool
        self._tracing_service: Optional[TracingServiceBase] = tracing_service

    def resolve(self, factory: OperationLayersFactoryBase) -> list[OperationLayerBase]:
        return [
            factory.create(OperationType.PLANNING, model = self._planning_model),
            factory.create(OperationType.DECOMPOSITION),
            factory.create(
                OperationType.SUBAGENTS,
                subagent_factory = self._subagent_factory,
                sandbox_pool = self._sandbox_pool,
                tracing_service = self._tracing_service
            ),
            factory.create(
                OperationType.MERGING,
                model = self._merging_model,
                tracing_service = self._tracing_service
            )
        ]
