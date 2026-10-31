from app.intelligence.memory import ContextWindowPolicy
from app.intelligence.memory import ContextWindowOperationSlide


class SlidePolicy(ContextWindowPolicy):
    """Always drops the two oldest messages, regardless of capacity, so a test can
    assert on a known transformation rather than on whatever a real policy decides."""

    def resolve(self, messages, capacity):
        return [ContextWindowOperationSlide(step = 2)]
