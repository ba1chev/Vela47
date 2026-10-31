from app.intelligence.agents import OperationPlan
from app.intelligence.agents import OperationStep
from app.intelligence.agents import OperationType
from app.intelligence.messages import MessageHuman
from app.intelligence.agents import OperationContext
from app.intelligence.agents import OperationSubagentType
from app.intelligence.agents import OperationDecompositionLayer


def make_context(*types):
    return OperationContext(
        goal = MessageHuman(content = "goal"),
        plan = OperationPlan(
            goal = "goal",
            steps = [OperationStep(index = i, description = f"step {i}", subagent_type = t)
                for i, t in enumerate(types)]
        )
    )


class TestOperationDecompositionLayer:
    def test_its_type_is_decomposition(self):
        assert OperationDecompositionLayer().operation_type is OperationType.DECOMPOSITION

    def test_one_task_per_step(self):
        context = make_context(OperationSubagentType.CODE, OperationSubagentType.TEST)
        OperationDecompositionLayer().execute(context)
        assert len(context.tasks) == 2

    def test_task_ids_are_unique(self):
        context = make_context(*[OperationSubagentType.CODE] * 5)
        OperationDecompositionLayer().execute(context)
        assert len({task.id for task in context.tasks}) == 5

    def test_the_step_index_is_carried_over(self):
        context = make_context(OperationSubagentType.CODE, OperationSubagentType.REVIEW)
        OperationDecompositionLayer().execute(context)
        assert [task.step_index for task in context.tasks] == [0, 1]

    def test_the_subagent_type_is_carried_over(self):
        context = make_context(OperationSubagentType.RESEARCH, OperationSubagentType.TEST)
        OperationDecompositionLayer().execute(context)
        assert [task.subagent_type for task in context.tasks] == [
            OperationSubagentType.RESEARCH, OperationSubagentType.TEST]

    def test_the_description_becomes_the_instruction(self):
        context = make_context(OperationSubagentType.CODE)
        OperationDecompositionLayer().execute(context)
        assert context.tasks[0].instruction == "step 0"

    def test_no_plan_produces_no_tasks_rather_than_an_error(self):
        context = OperationContext(goal = MessageHuman(content = "goal"))
        OperationDecompositionLayer().execute(context)
        assert context.tasks == []
