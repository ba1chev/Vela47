import time

from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageHuman
from tests.fixtures.agents.echo_agent import EchoAgent


class SlowEchoAgent(EchoAgent):
    """An EchoAgent that waits before it answers, the way a model call can stay silent
    for a while. Lets a stream test see what goes out to the browser while an agent
    produces nothing."""

    def __init__(self, delay_seconds: float, **kwargs) -> None:
        super().__init__(**kwargs)
        self._delay_seconds: float = delay_seconds

    def execute(self, human_message: MessageHuman) -> MessageAI:
        time.sleep(self._delay_seconds)
        return super().execute(human_message)
