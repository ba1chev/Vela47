from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageHuman
from tests.fixtures.agents.echo_agent import EchoAgent


class FailingEchoAgent(EchoAgent):
    """An EchoAgent whose run raises, the way a model or sandbox call can fail halfway.
    Lets a stream test see what reaches the browser and what reaches the server's log."""

    def execute(self, human_message: MessageHuman) -> MessageAI:
        raise RuntimeError("the model went away")
