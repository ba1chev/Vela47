from app.intelligence.messages import MessageAI
from app.intelligence.tools import ToolMessageWorkerInput
from app.intelligence.agents import OperationSubagentFactoryBase


class StubSubagentFactory(OperationSubagentFactoryBase):
    """Hands back an agent that answers immediately, recording which sandbox and peer
    tool each was given so a test can prove the lease reached the tool. Can be told to
    fail, for every type or for the types in fail_types, to exercise the layer's promise
    that one broken task does not sink the rest. An agent given a peer tool messages
    its peer once per entry in peer_messages before it answers."""

    def __init__(self, fail: bool = False, fail_types = (), peer_messages = ()) -> None:
        self.envs = []
        self.peer_tools = []
        self.agents = []
        self._fail = fail
        self._fail_types = set(fail_types)
        self._peer_messages = list(peer_messages)

    def create(self, type, sandbox_env, peer_tool = None):
        self.envs.append(sandbox_env)
        self.peer_tools.append(peer_tool)
        if self._fail or type in self._fail_types:
            raise RuntimeError("could not build agent")
        agent = _ImmediateAgent(type, peer_tool, self._peer_messages if peer_tool is not None else [])
        self.agents.append(agent)
        return agent


class _ImmediateAgent:
    evidence = ["checked by a stub"]

    def __init__(self, type, peer_tool, peer_messages) -> None:
        self.type = type
        self.received = []
        self.answers = []
        self._peer_tool = peer_tool
        self._peer_messages = peer_messages

    def execute(self, message) -> MessageAI:
        self.received.append(message.content)
        for current_message in self._peer_messages:
            self.answers.append(self._peer_tool.execute(ToolMessageWorkerInput(message = current_message)))
        return MessageAI(content = f"did {message.content}")
