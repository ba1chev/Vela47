from app.intelligence.a2a_interaction import A2AInteractionType
from app.intelligence.a2a_interaction import A2AInteractionBase


class RecordingA2AInteraction(A2AInteractionBase):
    """An interaction whose transport is a list: every text it carries is recorded with
    its sender and receiver and handed over unchanged, and every connect and disconnect
    is recorded too, so the exchange A2AInteractionBase defines can be tested alone."""

    def __init__(self) -> None:
        super().__init__()
        self.transfers = []
        self.events = []

    @property
    def interaction_type(self):
        return A2AInteractionType.HOST

    def _connect(self):
        self.events.append("connect")

    def _disconnect(self):
        self.events.append("disconnect")

    def _transfer(self, sender, receiver, text):
        self.transfers.append((sender, receiver, text))
        return text
