from app.messages.message_human import MessageHuman
from app.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType
from app.memory.short_term_memory.context_window.context_window_operation.context_window_policy_sliding_window import SlidingWindowPolicy


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
