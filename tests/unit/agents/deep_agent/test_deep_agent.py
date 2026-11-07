from app.intelligence.agents import DeepAgent
from app.intelligence.messages import MessageAI
from app.intelligence.agents import PromptManager
from app.intelligence.messages import MessageType
from app.intelligence.messages import MessageHuman
from app.intelligence.agents import OperationPipeline
from tests.fixtures.model.fake_model import FakeModel
from tests.fixtures.agents.static_policy import StaticPolicy
from tests.fixtures.agents.capturing_layer import CapturingLayer


def make_agent(contexts, max_context_window_size = 8, answer = "answer"):
    return DeepAgent(
        model = FakeModel(),
        prompt_manager = PromptManager(),
        max_context_window_size = max_context_window_size,
        operation_pipeline = OperationPipeline(StaticPolicy([CapturingLayer(contexts, answer)]))
    )


class TestDeepAgent:
    def test_the_first_turn_has_no_history(self):
        contexts = []
        make_agent(contexts).execute(MessageHuman(content = "hello"))
        assert contexts[0].history == []

    def test_the_current_goal_is_not_part_of_its_own_history(self):
        contexts = []
        make_agent(contexts).execute(MessageHuman(content = "hello"))
        assert contexts[0].goal.content == "hello"
        assert all(current.content != "hello" for current in contexts[0].history)

    def test_the_second_turn_sees_the_first_exchange_in_order(self):
        contexts = []
        agent = make_agent(contexts, answer = "first answer")
        agent.execute(MessageHuman(content = "first question"))
        agent.execute(MessageHuman(content = "follow-up"))
        history = contexts[1].history
        assert [current.content for current in history] == ["first question", "first answer"]
        assert [current.type for current in history] == [MessageType.HUMAN_MESSAGE, MessageType.AI_MESSAGE]

    def test_a_restored_conversation_becomes_the_history_of_the_next_turn(self):
        contexts = []
        agent = make_agent(contexts)
        agent.restore([MessageHuman(content = "earlier"), MessageAI(content = "reply")])
        agent.execute(MessageHuman(content = "now"))
        assert [current.content for current in contexts[0].history] == ["earlier", "reply"]

    def test_history_keeps_only_the_most_recent_messages(self):
        contexts = []
        agent = make_agent(contexts, max_context_window_size = 4)
        agent.restore([MessageHuman(content = f"m{index}") for index in range(10)])
        agent.execute(MessageHuman(content = "now"))
        assert [current.content for current in contexts[0].history] == ["m6", "m7", "m8", "m9"]

    def test_each_history_message_is_cut_to_the_limit(self):
        contexts = []
        agent = make_agent(contexts)
        agent.restore([MessageAI(content = "x" * (DeepAgent.HISTORY_MESSAGE_CHARS + 500))])
        agent.execute(MessageHuman(content = "now"))
        assert len(contexts[0].history[0].content) == DeepAgent.HISTORY_MESSAGE_CHARS

    def test_without_a_merged_answer_the_reply_is_empty_but_still_returned(self):
        reply = make_agent([], answer = None).execute(MessageHuman(content = "x"))
        assert reply.content == ""
