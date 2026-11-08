from app.intelligence.messages import MessageAI
from app.intelligence.agents import OperationPlan
from app.intelligence.agents import OperationStep
from app.intelligence.agents import OperationType
from app.intelligence.agents import OperationTask
from app.intelligence.messages import MessageHuman
from app.intelligence.tracing import TracingService
from app.intelligence.tracing import TraceEventType
from app.intelligence.agents import OperationContext
from tests.fixtures.model.fake_model import FakeModel
from app.intelligence.agents import OperationSubagentType
from app.intelligence.agents import OperationMergingLayer
from app.intelligence.agents import OperationSubagentResult


def make_context():
    return OperationContext(
        goal = MessageHuman(content = "compare things"),
        plan = OperationPlan(goal = "compare things", steps = [
            OperationStep(index = 0, description = "research it",
                subagent_type = OperationSubagentType.RESEARCH)]),
        results = [
            OperationSubagentResult(task_id = "t1",
                subagent_type = OperationSubagentType.RESEARCH,
                content = "found this"),
            OperationSubagentResult(task_id = "t2",
                subagent_type = OperationSubagentType.REVIEW,
                content = "it broke", status = "error")
        ])


class TestOperationMergingLayer:
    def test_its_type_is_merging(self):
        assert OperationMergingLayer(FakeModel()).operation_type is OperationType.MERGING

    def test_the_streamed_text_becomes_the_final_answer(self):
        context = make_context()
        OperationMergingLayer(FakeModel(["the merged answer"])).execute(context)
        assert context.final.content.strip() == "the merged answer"

    def test_the_goal_reaches_the_model(self):
        model = FakeModel(["answer"])
        OperationMergingLayer(model).execute(make_context())
        prompt = model.calls[0][0][1].content
        assert "compare things" in prompt

    def test_the_plan_reaches_the_model(self):
        model = FakeModel(["answer"])
        OperationMergingLayer(model).execute(make_context())
        assert "research it" in model.calls[0][0][1].content

    def test_failed_results_are_passed_through_not_hidden(self):
        model = FakeModel(["answer"])
        OperationMergingLayer(model).execute(make_context())
        prompt = model.calls[0][0][1].content
        assert "it broke" in prompt and "error" in prompt

    def test_each_chunk_is_reported_as_it_arrives(self):
        tracer = TracingService()
        OperationMergingLayer(FakeModel(["one two three"]), tracer).execute(make_context())
        chunks = [e for e in tracer.events() if e.type is TraceEventType.ANSWER_CHUNK]
        assert len(chunks) == 3

    def test_history_comes_before_the_report(self):
        model = FakeModel(["answer"])
        context = make_context()
        context.history = [MessageHuman(content = "earlier question"), MessageAI(content = "earlier answer")]
        OperationMergingLayer(model).execute(context)
        messages = model.calls[0][0]
        assert [current.content for current in messages[1:3]] == ["earlier question", "earlier answer"]
        assert "compare things" in messages[3].content

    def test_without_a_tracer_the_answer_is_still_complete(self):
        context = make_context()
        OperationMergingLayer(FakeModel(["one two three"])).execute(context)
        assert context.final.content.strip() == "one two three"

    def test_each_report_is_written_under_the_step_that_produced_it(self):
        model = FakeModel(["answer"])
        context = make_context()
        context.tasks = [
            OperationTask(id = "t1", step_index = 0, subagent_type = OperationSubagentType.RESEARCH, instruction = "find the prices"),
            OperationTask(id = "t2", step_index = 1, subagent_type = OperationSubagentType.REVIEW, instruction = "check prices.py")
        ]
        OperationMergingLayer(model).execute(context)
        report = model.calls[0][0][1].content
        assert "Step 1 (RESEARCH): find the prices\nReport (success): found this" in report
        assert "Step 2 (REVIEW): check prices.py\nReport (error): it broke" in report
        assert report.endswith("Write your answer to the user's request now.")

    def test_facts_the_system_checked_are_listed_under_their_report(self):
        model = FakeModel(["answer"])
        context = make_context()
        context.results[0] = context.results[0].model_copy(update = {"evidence": ["Pages read: https://a.org."]})
        OperationMergingLayer(model).execute(context)
        report = model.calls[0][0][1].content
        assert "Report (success): found this\nChecked by the system: Pages read: https://a.org." in report
