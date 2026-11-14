from app.intelligence.agents import A2AInteractionType
from app.intelligence.agents import A2AInteractionBase


class RecordingA2AInteraction(A2AInteractionBase):
    """An interaction whose transport is a list: every text it carries is recorded with
    its sender and receiver and handed over unchanged, and every connect and disconnect
    is recorded too, so the exchange A2AInteractionBase defines can be tested alone.
    fail_connect makes connecting raise, like a Docker network that cannot be created."""

    def __init__(self, fail_connect = False) -> None:
        super().__init__()
        self.transfers = []
        self.events = []
        self._fail_connect = fail_connect

    @property
    def interaction_type(self):
        return A2AInteractionType.HOST

    def _connect(self):
        if self._fail_connect:
            raise RuntimeError("no network for the pair")
        self.events.append("connect")

    def _disconnect(self):
        self.events.append("disconnect")

    def _transfer(self, sender, receiver, text):
        self.transfers.append((sender, receiver, text))
        return text
