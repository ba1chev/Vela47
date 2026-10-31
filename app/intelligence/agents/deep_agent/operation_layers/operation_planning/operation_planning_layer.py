import json

from app.intelligence.messages.message_system import MessageSystem
from app.intelligence.agents.deep_agent.operation_context import OperationContext
from app.intelligence.agents.deep_agent.system_prompt import PLANNING_SYSTEM_PROMPT
from app.intelligence.model.model_foundation.model_foundation import ModelFoundation
from app.intelligence.outputs.output_parser.output_parser_structured import OutputParserStructured
from app.intelligence.agents.deep_agent.operation_layers.operation_layer_type import OperationType
from app.intelligence.agents.deep_agent.operation_layers.operation_layer_base import OperationLayerBase
from app.intelligence.agents.deep_agent.operation_layers.operation_planning.operation_plan import OperationPlan
from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_type import OperationSubagentType


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
                subagent_types = ", ".join(current.name for current in OperationSubagentType),
                schema = json.dumps(OperationPlan.model_json_schema(), indent = 2)
            )
        )

    def execute(self, context: OperationContext) -> None:
        response = self._model.invoke([self._build_system_message(), context.goal])
        context.plan = self._parser.parse(response).data
