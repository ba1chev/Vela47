from app.intelligence.agents import AgentBase
from app.intelligence.model import ModelConfig
from app.intelligence.messages import MessageAI
from app.intelligence.agents import PromptManager
from app.intelligence.messages import MessageHuman
from app.intelligence.model import ModelFoundation
from app.intelligence.messages import MessageSystem
from tests.fixtures.agents.echo_agent import EchoAgent
from app.intelligence.memory import ContextWindowPolicy
from app.intelligence.memory import SlidingWindowPolicy
from tests.fixtures.memory.keep_all_policy import KeepAllPolicy


def make_agent(policy = None, max_size = 10, prompt_manager = None):
    config = ModelConfig(model_name = "qwen3:1.7b")
    agent = EchoAgent(
        model = ModelFoundation(config = config),
        prompt_manager = prompt_manager or PromptManager(),
        max_context_window_size = max_size,
    )
    agent._context_window.set_policy(policy or KeepAllPolicy())
    return agent


class TestAgent:
    def test_memory_starts_empty(self):
        agent = make_agent()
        assert len(agent._short_term_memory) == 0

    def test_execute_appends_to_memory(self):
        agent = make_agent()
        agent.execute(MessageHuman(content = "hello"))
        assert len(agent._short_term_memory) == 2

    def test_execute_returns_ai_message(self):
        agent = make_agent()
        result = agent.execute(MessageHuman(content = "ping"))
        assert isinstance(result, MessageAI)

    def test_response_content_correct(self):
        agent = make_agent()
        result = agent.execute(MessageHuman(content = "ping"))
        assert result.content == "Echo: ping"

    def test_multiple_turns_accumulate_memory(self):
        agent = make_agent()
        agent.execute(MessageHuman(content = "a"))
        agent.execute(MessageHuman(content = "b"))
        assert len(agent._short_term_memory) == 4

    def test_system_prompts_prepended_to_context(self):
        pm = PromptManager()
        pm.register("sys", "Be helpful.")
        captured = []

        class CapturingAgent(AgentBase):
            def execute(self, human_message):
                self._append_human(human_message)
                msgs = self._build_messages()
                captured.extend(msgs)
                response = MessageAI(content = "ok")
                self._append_ai(response)
                return response

        config = ModelConfig(model_name = "qwen3:1.7b")
        agent = CapturingAgent(
            model = ModelFoundation(config = config),
            prompt_manager = pm,
            max_context_window_size = 10,
        )
        agent._context_window.set_policy(KeepAllPolicy())
        agent.execute(MessageHuman(content = "hi"))
        assert isinstance(captured[0], MessageSystem)
        assert captured[0].content == "Be helpful."

    def test_sliding_window_policy_evicts_oldest(self):
        agent = make_agent(policy = SlidingWindowPolicy(step = 2), max_size = 4)
        for i in range(3):
            agent.execute(MessageHuman(content = f"msg {i}"))
        agent._context_window.update()
        context = agent._context_window.build()
        assert len(context) <= 4

    def test_context_window_is_full_after_filling(self):
        agent = make_agent(max_size = 2)
        agent.execute(MessageHuman(content = "fills it"))
        assert agent._context_window.is_full()

    def test_tool_executor_none_without_registry(self):
        agent = make_agent()
        assert agent._tool_executor is None

    def test_vector_db_memory_none_by_default(self):
        agent = make_agent()
        assert agent._vector_db_memory is None
