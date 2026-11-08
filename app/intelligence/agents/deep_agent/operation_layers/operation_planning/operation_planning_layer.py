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
    model must produce is generated from OperationPlan itself and passed to the model
    as output_schema, so its decoding is held to the same contract the pipeline
    parses — adding a field to the plan changes what the model can write without
    anyone touching the prompt.

    The schema is not pasted into the prompt. It describes the plan to developers —
    its descriptions name factories and layers — and a small model given three
    thousand characters of it, with the subagent types as bare numbers, planned
    worse and at times copied the schema back instead of filling it in. The prompt
    shows the shape through two short example plans instead, and a test keeps every
    field of the schema named in it.

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
            content = PLANNING_SYSTEM_PROMPT.format(subagent_types = format_subagent_capabilities())
        )

    def execute(self, context: OperationContext) -> None:
        response = self._model.invoke(
            [self._build_system_message(), *context.history, context.goal],
            output_schema = self._schema
        )
        context.plan = self._parser.parse(response).data
