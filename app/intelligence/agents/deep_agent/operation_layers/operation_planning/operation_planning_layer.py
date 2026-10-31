import json

from app.intelligence.messages import MessageSystem
from app.intelligence.agents import OperationContext
from app.intelligence.model import ModelFoundation
from app.intelligence.outputs import OutputParserStructured
from app.intelligence.agents import OperationType
from app.intelligence.agents import PLANNING_SYSTEM_PROMPT
from app.intelligence.agents import OperationLayerBase
from app.intelligence.agents import format_subagent_capabilities
from app.intelligence.agents import OperationPlan


class OperationPlanningLayer(OperationLayerBase):
    """Turns the user's goal into a structured OperationPlan. The JSON schema the
    model is asked to produce is generated from OperationPlan itself and injected
    into the prompt, so the contract the model is held to and the contract the
    pipeline parses can never drift apart — adding a field to the plan updates
    the prompt automatically.

    Parsing is delegated to OutputParserStructured, which means a malformed plan
    raises a ValidationError here rather than surfacing as a confusing failure
    three layers later."""

    def __init__(self, model: ModelFoundation) -> None:
        self._model: ModelFoundation = model
        self._parser: OutputParserStructured[OperationPlan] = OutputParserStructured(
            schema = OperationPlan
        )

    @property
    def operation_type(self) -> OperationType:
        return OperationType.PLANNING

    def _build_system_message(self) -> MessageSystem:
        return MessageSystem(
            content = PLANNING_SYSTEM_PROMPT.format(
                subagent_types = format_subagent_capabilities(),
                schema = json.dumps(OperationPlan.model_json_schema(), indent = 2)
            )
        )

    def execute(self, context: OperationContext) -> None:
        response = self._model.invoke([self._build_system_message(), context.goal])
        context.plan = self._parser.parse(response).data
