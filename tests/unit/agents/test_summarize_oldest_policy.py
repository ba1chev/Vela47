from app.intelligence.messages import MessageHuman
from app.intelligence.messages import MessageSystem
from app.intelligence.memory import SummarizeOldestPolicy
from app.intelligence.memory import ContextWindowOperationType


class TestSummarizeOldestPolicy:
    def test_resolve_returns_summarize_operation(self):
        policy = SummarizeOldestPolicy(n = 2, summarizer = lambda m: "summary")
        ops = policy.resolve([], capacity = 5)
        assert len(ops) == 1
        assert ops[0].operation_type == ContextWindowOperationType.SUMMARIZE

    def test_end_to_end_compression(self):
        msgs = [MessageHuman(content = f"turn {i}") for i in range(5)]
        policy = SummarizeOldestPolicy(
            n = 3,
            summarizer = lambda ms: "Compressed: " + ", ".join(m.content for m in ms)
        )
        ops = policy.resolve(msgs, capacity = 5)
        result = ops[0].apply(msgs)
        assert len(result) == 3
        assert isinstance(result[0], MessageSystem)
        assert "turn 0" in result[0].content
