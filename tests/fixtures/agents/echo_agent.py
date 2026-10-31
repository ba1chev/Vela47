from app.intelligence.agents import AgentBase
from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageHuman


class EchoAgent(AgentBase):
    """The smallest possible concrete agent: it runs the full append/build/append
    cycle AgentBase defines but answers from a template instead of calling a model,
    so the base class can be tested without Ollama running."""

    def execute(self, human_message: MessageHuman) -> MessageAI:
        self._append_human(human_message)
        self._build_messages()
        response = MessageAI(content = f"Echo: {human_message.content}")
        self._append_ai(response)
        return response
