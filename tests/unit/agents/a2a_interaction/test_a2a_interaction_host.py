from app.intelligence.model import ModelConfig
from app.intelligence.agents import PromptManager
from app.intelligence.messages import MessageHuman
from app.intelligence.model import ModelFoundation
from app.intelligence.agents import A2AInteractionHost
from app.intelligence.agents import A2AInteractionType
from tests.fixtures.agents.echo_agent import EchoAgent


def make_agent():
    return EchoAgent(
        model = ModelFoundation(config = ModelConfig(model_name = "qwen3:1.7b")),
        prompt_manager = PromptManager(),
        max_context_window_size = 10
    )


def make_interaction():
    interaction = A2AInteractionHost()
    interaction.append_left(make_agent())
    interaction.append_right(make_agent())
    return interaction


class TestA2AInteractionHost:
    def test_it_is_the_host_type(self):
        assert A2AInteractionHost().interaction_type is A2AInteractionType.HOST

    def test_the_message_and_its_answer_cross_unchanged(self):
        with make_interaction() as interaction:
            assert interaction.send(interaction.left, MessageHuman(content = "здравей")).content == "Echo: здравей"

    def test_connecting_and_closing_only_change_its_state(self):
        interaction = make_interaction()
        interaction.establish_connection()
        assert interaction.connected
        interaction.close_connection()
        assert not interaction.connected
