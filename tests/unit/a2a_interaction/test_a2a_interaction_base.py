import pytest

from app.intelligence.model import ModelConfig
from app.intelligence.agents import PromptManager
from app.intelligence.messages import MessageHuman
from app.intelligence.model import ModelFoundation
from tests.fixtures.agents.echo_agent import EchoAgent
from tests.fixtures.a2a_interaction.recording_a2a_interaction import RecordingA2AInteraction


def make_agent():
    return EchoAgent(
        model = ModelFoundation(config = ModelConfig(model_name = "qwen3:1.7b")),
        prompt_manager = PromptManager(),
        max_context_window_size = 10
    )


def make_interaction(connected = True):
    interaction = RecordingA2AInteraction()
    interaction.append_left(make_agent())
    interaction.append_right(make_agent())
    if connected:
        interaction.establish_connection()
    return interaction


class TestA2AInteractionBase:
    def test_it_holds_one_agent_on_each_side(self):
        left, right = make_agent(), make_agent()
        interaction = RecordingA2AInteraction()
        interaction.append_left(left)
        interaction.append_right(right)
        assert interaction.left is left and interaction.right is right

    def test_a_side_holds_one_agent_only(self):
        interaction = make_interaction(connected = False)
        with pytest.raises(ValueError, match = "already holds an agent"):
            interaction.append_left(make_agent())

    def test_the_same_agent_cannot_be_on_both_sides(self):
        agent = make_agent()
        interaction = RecordingA2AInteraction()
        interaction.append_left(agent)
        with pytest.raises(ValueError, match = "already part of this interaction"):
            interaction.append_right(agent)

    def test_connecting_needs_an_agent_on_each_side(self):
        interaction = RecordingA2AInteraction()
        interaction.append_left(make_agent())
        with pytest.raises(RuntimeError, match = "append both"):
            interaction.establish_connection()

    def test_sending_before_connecting_is_refused(self):
        interaction = make_interaction(connected = False)
        with pytest.raises(RuntimeError, match = "not connected"):
            interaction.send(interaction.left, MessageHuman(content = "hi"))

    def test_the_message_reaches_the_other_agent_and_its_answer_comes_back(self):
        interaction = make_interaction()
        reply = interaction.send(interaction.left, MessageHuman(content = "hi"))
        assert reply.content == "Echo: hi"
        assert [current.content for current in interaction.right._short_term_memory.get_all()] == ["hi", "Echo: hi"]
        assert len(interaction.left._short_term_memory) == 0

    def test_either_side_can_send(self):
        interaction = make_interaction()
        assert interaction.send(interaction.right, MessageHuman(content = "back")).content == "Echo: back"

    def test_every_exchange_crosses_the_connection_both_ways(self):
        interaction = make_interaction()
        left, right = interaction.left, interaction.right
        interaction.send(left, MessageHuman(content = "hi"))
        assert interaction.transfers == [(left, right, "hi"), (right, left, "Echo: hi")]

    def test_an_agent_outside_the_interaction_cannot_send(self):
        with pytest.raises(ValueError, match = "not one of this interaction's agents"):
            make_interaction().send(make_agent(), MessageHuman(content = "hi"))

    def test_with_connects_and_closes_even_when_the_block_raises(self):
        interaction = make_interaction(connected = False)
        with pytest.raises(KeyError):
            with interaction:
                assert interaction.connected
                raise KeyError("boom")
        assert interaction.events == ["connect", "disconnect"] and not interaction.connected

    def test_connecting_twice_and_closing_twice_happen_once(self):
        interaction = make_interaction()
        interaction.establish_connection()
        interaction.close_connection()
        interaction.close_connection()
        assert interaction.events == ["connect", "disconnect"]
