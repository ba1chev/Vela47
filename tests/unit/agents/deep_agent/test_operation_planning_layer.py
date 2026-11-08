import json
import pytest
from pydantic import ValidationError

from app.intelligence.messages import MessageAI
from app.intelligence.agents import OperationType
from app.intelligence.messages import MessageType
from app.intelligence.agents import OperationPlan
from app.intelligence.messages import MessageHuman
from app.intelligence.agents import OperationContext
from tests.fixtures.model.fake_model import FakeModel
from app.intelligence.agents import OperationSubagentType
from app.intelligence.agents import OperationPlanningLayer

PLAN = json.dumps({
    "goal": "add tests",
    "steps": [{"index": 0, "description": "write the tests", "subagent_type": OperationSubagentType.TEST.value}]
})


class TestOperationPlanningLayer:
    def test_its_type_is_planning(self):
        assert OperationPlanningLayer(FakeModel()).operation_type is OperationType.PLANNING

    def test_the_model_reply_becomes_the_plan(self):
        context = OperationContext(goal = MessageHuman(content = "add tests"))
        OperationPlanningLayer(FakeModel([PLAN])).execute(context)
        assert context.plan.steps[0].subagent_type is OperationSubagentType.TEST

    def test_without_history_the_model_sees_the_prompt_and_the_goal(self):
        model = FakeModel([PLAN])
        OperationPlanningLayer(model).execute(OperationContext(goal = MessageHuman(content = "add tests")))
        messages = model.calls[0][0]
        assert [current.type for current in messages] == [MessageType.SYSTEM_MESSAGE, MessageType.HUMAN_MESSAGE]

    def test_history_sits_between_the_prompt_and_the_goal(self):
        model = FakeModel([PLAN])
        context = OperationContext(
            goal = MessageHuman(content = "now add tests for it"),
            history = [MessageHuman(content = "write a sort"), MessageAI(content = "here is sort.py")]
        )
        OperationPlanningLayer(model).execute(context)
        assert [current.content for current in model.calls[0][0][1:]] == [
            "write a sort", "here is sort.py", "now add tests for it"
        ]

    def test_the_plan_schema_constrains_the_models_reply(self):
        model = FakeModel([PLAN])
        OperationPlanningLayer(model).execute(OperationContext(goal = MessageHuman(content = "add tests")))
        assert model.output_schemas == [OperationPlan.model_json_schema()]

    def test_the_prompt_tells_the_planner_what_history_is_for(self):
        model = FakeModel([PLAN])
        OperationPlanningLayer(model).execute(OperationContext(goal = MessageHuman(content = "x")))
        assert "Earlier turns of the conversation" in model.calls[0][0][0].content

    def test_a_malformed_plan_raises_here_rather_than_later(self):
        with pytest.raises(ValidationError):
            OperationPlanningLayer(FakeModel(["not json"])).execute(OperationContext(goal = MessageHuman(content = "x")))
