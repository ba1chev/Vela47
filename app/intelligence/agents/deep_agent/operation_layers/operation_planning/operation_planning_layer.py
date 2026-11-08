import json

from app.intelligence.agents import OperationType
from app.intelligence.agents import OperationPlan
from app.intelligence.model import ModelFoundation
from app.intelligence.messages import MessageSystem
from app.intelligence.agents import OperationContext
from app.intelligence.agents import OperationLayerBase
from app.intelligence.agents import PLANNING_SYSTEM_PROMPT
from app.intelligence.outputs import OutputParserStructured
from app.intelligence.agents import format_subagent_capabilities


class OperationPlanningLayer(OperationLayerBase):
    """Turns the user's goal into a structured OperationPlan. The JSON schema the
    model is asked to produce is generated from OperationPlan itself and injected
    into the prompt, so the contract the model is held to and the contract the
    pipeline parses can never drift apart — adding a field to the plan updates
    the prompt automatically.

    The same schema is passed to the model as output_schema, so its decoding is held to
    it as well. A small model shown a schema in its prompt sometimes copies the schema
    back instead of filling it in — for some goals every time — and that reply can never
    become a plan. The prompt keeps the schema anyway, because the field descriptions in
    it are what tell the model what to write.

    Parsing is delegated to OutputParserStructured, which means a malformed plan
    raises a ValidationError here rather than surfacing as a confusing failure
    three layers later.

    The conversation's earlier turns sit between the system prompt and the goal, in
    the order they happened, so a goal like 'now add tests for it' can be planned
    against what 'it' was."""

    def __init__(self, model: ModelFoundation) -> None:
        self._model: ModelFoundation = model
        self._schema: dict = OperationPlan.model_json_schema()
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
                schema = json.dumps(self._schema, indent = 2)
            )
        )

    def execute(self, context: OperationContext) -> None:
        response = self._model.invoke(
            [self._build_system_message(), *context.history, context.goal],
            output_schema = self._schema
        )
        context.plan = self._parser.parse(response).data
