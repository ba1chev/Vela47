import pytest

from app.intelligence.model import ModelConfig
from app.intelligence.agents import PromptManager
from app.intelligence.model import ModelFoundation
from tests.fixtures.agents.echo_agent import EchoAgent
from app.intelligence.a2a_interaction import A2AInteractionType
from app.intelligence.a2a_interaction import A2AInteractionDocker


def make_agent():
    return EchoAgent(
        model = ModelFoundation(config = ModelConfig(model_name = "qwen3:1.7b")),
        prompt_manager = PromptManager(),
        max_context_window_size = 10
    )


class TestA2AInteractionDocker:
    def test_it_is_the_docker_type(self):
        assert A2AInteractionDocker("vela47-slot-0", "vela47-slot-1").interaction_type is A2AInteractionType.DOCKER

    def test_every_interaction_gets_a_network_of_its_own(self):
        first = A2AInteractionDocker("vela47-slot-0", "vela47-slot-1")
        second = A2AInteractionDocker("vela47-slot-0", "vela47-slot-1")
        assert first.network.startswith("vela47-a2a-") and first.network != second.network

    def test_two_agents_in_one_container_are_refused(self):
        with pytest.raises(ValueError, match = "need a container each"):
            A2AInteractionDocker("vela47-slot-0", "vela47-slot-0")

    def test_each_agent_is_reached_in_its_own_container(self):
        interaction = A2AInteractionDocker("vela47-slot-0", "vela47-slot-1")
        left, right = make_agent(), make_agent()
        interaction.append_left(left)
        interaction.append_right(right)
        assert interaction._container_of(left) == "vela47-slot-0" and interaction._container_of(right) == "vela47-slot-1"
