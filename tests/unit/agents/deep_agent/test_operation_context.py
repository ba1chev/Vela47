from app.intelligence.messages import MessageHuman
from app.intelligence.agents import OperationContext


class TestOperationContext:
    def test_only_the_goal_is_required(self):
        context = OperationContext(goal = MessageHuman(content = "do a thing"))
        assert context.plan is None and context.final is None
        assert context.tasks == [] and context.results == []
        assert context.history == []

    def test_run_id_is_generated(self):
        assert OperationContext(goal = MessageHuman(content = "x")).run_id

    def test_each_context_gets_its_own_run_id(self):
        first = OperationContext(goal = MessageHuman(content = "x"))
        second = OperationContext(goal = MessageHuman(content = "x"))
        assert first.run_id != second.run_id

    def test_it_is_mutable(self):
        context = OperationContext(goal = MessageHuman(content = "x"))
        context.final = None
        context.tasks = []
        assert context.tasks == []
