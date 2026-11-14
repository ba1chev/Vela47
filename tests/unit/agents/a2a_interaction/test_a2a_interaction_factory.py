import pytest

from app.intelligence.agents import A2AInteractionHost
from app.intelligence.agents import A2AInteractionType
from app.intelligence.agents import A2AInteractionDocker
from app.intelligence.agents import A2AInteractionFactory
from app.intelligence.agents import A2A_INTERACTION_REGISTRY


class TestA2AInteractionFactory:
    def test_every_type_is_registered(self):
        assert set(A2A_INTERACTION_REGISTRY) == set(A2AInteractionType)

    def test_host_needs_nothing(self):
        assert isinstance(A2AInteractionFactory().create(A2AInteractionType.HOST), A2AInteractionHost)

    def test_docker_is_given_its_two_containers(self):
        interaction = A2AInteractionFactory().create(
            A2AInteractionType.DOCKER, left_container = "vela47-slot-0", right_container = "vela47-slot-1"
        )
        assert isinstance(interaction, A2AInteractionDocker)
        assert interaction._left_container == "vela47-slot-0" and interaction._right_container == "vela47-slot-1"

    def test_every_call_builds_a_new_interaction(self):
        factory = A2AInteractionFactory()
        assert factory.create(A2AInteractionType.HOST) is not factory.create(A2AInteractionType.HOST)

    def test_an_unknown_type_is_refused(self):
        with pytest.raises(ValueError, match = "No interaction class registered"):
            A2AInteractionFactory().create("carrier pigeon")
