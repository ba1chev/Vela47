from app.intelligence.messages import MessageAI


class FakeModel:
    """Returns scripted replies instead of calling Ollama, and records what it was
    asked. Satisfies the shape ModelFoundation exposes — invoke and stream — without
    inheriting it, because the real class opens a connection in neither but does ask
    a config for a model name that would not exist."""

    def __init__(self, replies = None) -> None:
        self._replies = list(replies or [])
        self.calls = []

    def invoke(self, messages, tools = None) -> MessageAI:
        self.calls.append((messages, tools))
        content = self._replies.pop(0) if self._replies else "fallback"
        return MessageAI(content = content)

    def stream(self, messages):
        self.calls.append((messages, None))
        reply = self._replies.pop(0) if self._replies else "fallback"
        for word in reply.split(" "):
            yield word + " "
