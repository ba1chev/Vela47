from typing import Optional, Self
from abc import ABC, abstractmethod

from app.intelligence.agents import AgentBase
from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageBase
from app.intelligence.messages import MessageHuman
from app.intelligence.a2a_interaction import A2AInteractionType


class A2AInteractionBase(ABC):
    """Two agents and the way a message gets from one to the other. Binary on purpose:
    a left and a right agent and nothing else, so every exchange has one sender and one
    receiver, and a conversation among more agents is several interactions.

    send() is the exchange: the message travels to the other agent, which answers it
    with execute(), and the answer travels back. How a text travels is the one thing
    the types differ on, so _transfer() is abstract, and so are _connect() and
    _disconnect(), which set up and tear down what it travels over. `with` does both."""

    def __init__(self) -> None:
        self._left: Optional[AgentBase] = None
        self._right: Optional[AgentBase] = None
        self._connected: bool = False

    @property
    @abstractmethod
    def interaction_type(self) -> A2AInteractionType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def _connect(self) -> None:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def _disconnect(self) -> None:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def _transfer(self, sender: AgentBase, receiver: AgentBase, text: str) -> str:
        raise NotImplementedError("Must be implemented")

    @property
    def left(self) -> Optional[AgentBase]:
        return self._left

    @property
    def right(self) -> Optional[AgentBase]:
        return self._right

    @property
    def connected(self) -> bool:
        return self._connected

    def append_left(self, agent: AgentBase) -> None:
        self._check_appendable(self._left, agent)
        self._left = agent

    def append_right(self, agent: AgentBase) -> None:
        self._check_appendable(self._right, agent)
        self._right = agent

    def _check_appendable(self, side: Optional[AgentBase], agent: AgentBase) -> None:
        if side is not None:
            raise ValueError("That side of the interaction already holds an agent.")
        if agent is self._left or agent is self._right:
            raise ValueError("The agent is already part of this interaction.")

    def establish_connection(self) -> None:
        if self._left is None or self._right is None:
            raise RuntimeError("An interaction connects two agents; append both before connecting.")
        if self._connected:
            return
        self._connect()
        self._connected = True

    def close_connection(self) -> None:
        if not self._connected:
            return
        self._connected = False
        self._disconnect()

    def send(self, sender: AgentBase, message: MessageHuman) -> MessageAI:
        if not self._connected:
            raise RuntimeError("The interaction is not connected; call establish_connection() first.")

        receiver = self._receiver_of(sender)
        delivered = self._transfer(sender, receiver, self._text(message))
        reply = receiver.execute(MessageHuman(content = delivered))
        return MessageAI(content = self._transfer(receiver, sender, self._text(reply)))

    def _receiver_of(self, sender: AgentBase) -> AgentBase:
        if sender is self._left:
            return self._right
        if sender is self._right:
            return self._left
        raise ValueError("The sender is not one of this interaction's agents.")

    def _text(self, message: MessageBase) -> str:
        return message.content if isinstance(message.content, str) else str(message.content)

    def __enter__(self) -> Self:
        self.establish_connection()
        return self

    def __exit__(self, *exception: object) -> None:
        self.close_connection()
