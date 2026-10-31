from app.intelligence.memory import ContextWindowPolicy


class KeepAllPolicy(ContextWindowPolicy):
    """Resolves to no operations, so the window is left exactly as memory holds it.
    Lets a test observe the window without a policy also changing it."""

    def resolve(self, messages, capacity):
        return []
