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
    """Turns the user's goal into an OperationPlan. The JSON schema is generated from
    OperationPlan and passed as output_schema, so decoding is held to the contract the
    pipeline parses, and OutputParserStructured makes a malformed plan raise here rather
    than three layers later.

    The schema is not pasted into the prompt: written for developers, it made a small
    model plan worse and sometimes copy it back. Two short example plans show the shape
    instead, and a test keeps every schema field named in the prompt. Earlier turns sit
    between the system prompt and the goal, so 'now add tests for it' can be planned.
    A plan holds at most MAX_STEPS steps: the schema says so, and a longer one is cut,
    since not every backend holds decoding to the schema."""

    MAX_STEPS = 4

    def __init__(self, model: ModelFoundation) -> None:
        self._model: ModelFoundation = model
        self._schema: dict = OperationPlan.model_json_schema()
        self._schema["properties"]["steps"]["maxItems"] = self.MAX_STEPS
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
        plan = self._parser.parse(response).data
        context.plan = plan.model_copy(update = {"steps": plan.steps[:self.MAX_STEPS]})
