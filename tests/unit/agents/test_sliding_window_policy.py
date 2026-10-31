from app.intelligence.messages import MessageHuman
from app.intelligence.memory import SlidingWindowPolicy
from app.intelligence.memory import ContextWindowOperationType


class TestSlidingWindowPolicy:
    def test_resolve_returns_slide_operation(self):
        policy = SlidingWindowPolicy(step = 3)
        ops = policy.resolve([], capacity = 5)
        assert len(ops) == 1
        assert ops[0].operation_type == ContextWindowOperationType.SLIDE

    def test_step_propagated(self):
        msgs = [MessageHuman(content = str(i)) for i in range(5)]
        policy = SlidingWindowPolicy(step = 3)
        ops = policy.resolve(msgs, capacity = 5)
        result = ops[0].apply(msgs)
        assert len(result) == 2
        assert result[0].content == "3"
