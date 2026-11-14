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
        expected = OperationPlan.model_json_schema()
        expected["properties"]["steps"]["maxItems"] = OperationPlanningLayer.MAX_STEPS
        assert model.output_schemas == [expected]

    def test_a_plan_longer_than_the_cap_is_cut(self):
        steps = [{"index": index, "description": f"look up part {index}", "subagent_type": "RESEARCH"} for index in range(6)]
        context = OperationContext(goal = MessageHuman(content = "compare six things"))
        OperationPlanningLayer(FakeModel([json.dumps({"goal": "compare", "steps": steps})])).execute(context)
        assert [current.index for current in context.plan.steps] == [0, 1, 2, 3]

    def test_a_request_that_needs_no_worker_gets_an_empty_plan(self):
        context = OperationContext(goal = MessageHuman(content = "hi, I am Yoan"))
        OperationPlanningLayer(FakeModel([json.dumps({"goal": "Greet Yoan", "steps": []})])).execute(context)
        assert context.plan.steps == []

    def test_the_prompt_shows_an_empty_plan(self):
        model = FakeModel([PLAN])
        OperationPlanningLayer(model).execute(OperationContext(goal = MessageHuman(content = "hi")))
        assert '"steps": []' in model.calls[0][0][0].content

    def test_the_prompt_tells_the_planner_what_history_is_for(self):
        model = FakeModel([PLAN])
        OperationPlanningLayer(model).execute(OperationContext(goal = MessageHuman(content = "x")))
        assert "Earlier turns of the conversation" in model.calls[0][0][0].content

    def test_a_malformed_plan_raises_here_rather_than_later(self):
        with pytest.raises(ValidationError):
            OperationPlanningLayer(FakeModel(["not json"])).execute(OperationContext(goal = MessageHuman(content = "x")))

    def test_the_prompt_names_every_field_and_type_the_plan_schema_allows(self):
        model = FakeModel([PLAN])
        OperationPlanningLayer(model).execute(OperationContext(goal = MessageHuman(content = "x")))
        prompt = model.calls[0][0][0].content
        fields = {"goal", "steps", *OperationPlan.model_json_schema()["$defs"]["OperationStep"]["properties"]}
        assert all(f'"{current}"' in prompt for current in fields)
        assert all(current.name in prompt for current in OperationSubagentType)

    def test_the_schema_constrains_the_reply_but_is_not_pasted_into_the_prompt(self):
        model = FakeModel([PLAN])
        OperationPlanningLayer(model).execute(OperationContext(goal = MessageHuman(content = "x")))
        assert "$defs" not in model.calls[0][0][0].content and "$defs" in model.output_schemas[0]

    def test_subagent_types_are_written_by_name(self):
        allowed = OperationPlan.model_json_schema()["$defs"]["OperationSubagentType"]["enum"]
        assert allowed == ["RESEARCH", "CODE", "TEST", "REVIEW"]
