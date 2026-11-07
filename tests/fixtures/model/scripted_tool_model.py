from app.intelligence.messages import MessageAI


class ScriptedToolModel:
    """Returns scripted MessageAI replies — tool calls included — instead of calling
    Ollama, and records the messages and tool schemas of every call. Lets a ReAct loop be
    driven through specific tool calls and its history inspected afterwards. With the
    script exhausted it answers 'done' and calls nothing."""

    def __init__(self, replies = None) -> None:
        self._replies = list(replies or [])
        self.calls = []

    def invoke(self, messages, tools = None):
        self.calls.append((list(messages), tools))
        return self._replies.pop(0) if self._replies else MessageAI(content = "done")
