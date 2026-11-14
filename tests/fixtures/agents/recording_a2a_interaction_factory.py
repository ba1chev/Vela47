from tests.fixtures.agents.recording_a2a_interaction import RecordingA2AInteraction


class RecordingA2AInteractionFactory:
    """Builds RecordingA2AInteraction whatever the type, and records each type and the
    keyword arguments it was asked for, so a test can see which containers a Docker
    interaction would have connected without starting one. fail_connect makes every
    interaction it builds refuse to connect."""

    def __init__(self, fail_connect = False) -> None:
        self.created = []
        self.interactions = []
        self._fail_connect = fail_connect

    def create(self, type, **kwargs):
        self.created.append((type, kwargs))
        interaction = RecordingA2AInteraction(fail_connect = self._fail_connect)
        self.interactions.append(interaction)
        return interaction
