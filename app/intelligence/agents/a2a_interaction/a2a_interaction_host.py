from app.intelligence.agents import AgentBase
from app.intelligence.agents import A2AInteractionType
from app.intelligence.agents import A2AInteractionBase


class A2AInteractionHost(A2AInteractionBase):
    """Two agents in the same process, a text handed from one to the other unchanged.
    There is nothing to set up or tear down, so connecting and disconnecting do
    nothing. It is the interaction a deep agent uses when its sandbox has no containers
    to carry a message through (see SandboxPoolInMemory), and the exchange itself is
    still the one A2AInteractionBase defines."""

    @property
    def interaction_type(self) -> A2AInteractionType:
        return A2AInteractionType.HOST

    def _connect(self) -> None:
        return None

    def _disconnect(self) -> None:
        return None

    def _transfer(self, sender: AgentBase, receiver: AgentBase, text: str) -> str:
        return text
