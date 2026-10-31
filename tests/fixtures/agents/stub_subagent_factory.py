from app.intelligence.messages import MessageAI
from app.intelligence.agents import OperationSubagentFactoryBase


class StubSubagentFactory(OperationSubagentFactoryBase):
    """Hands back an agent that answers immediately, recording which sandbox each
    was given so a test can prove the lease reached the tool. Can be told to fail,
    to exercise the layer's promise that one broken task does not sink the rest."""

    def __init__(self, fail: bool = False) -> None:
        self.envs = []
        self._fail = fail

    def create(self, type, sandbox_env):
        self.envs.append(sandbox_env)
        if self._fail:
            raise RuntimeError("could not build agent")
        return _ImmediateAgent()


class _ImmediateAgent:
    def execute(self, message) -> MessageAI:
        return MessageAI(content = f"did {message.content}")
