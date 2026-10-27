from app.agents.agent_base import Agent
from app.messages.message_ai import MessageAI
from app.messages.message_human import MessageHuman
from app.messages.message_system import MessageSystem
from app.agents.prompts.prompt_manager import PromptManager
from app.model.model_config import ModelConfig
from app.model.model_foundation.model_foundation import ModelFoundation
from app.memory.short_term_memory.context_window.context_window_operation.context_window_policy import ContextWindowPolicy
from app.memory.short_term_memory.context_window.context_window_operation.context_window_policy_sliding_window import SlidingWindowPolicy


class KeepAllPolicy(ContextWindowPolicy):
    def resolve(self, messages, capacity): return []


class EchoAgent(Agent):
    def execute(self, human_message: MessageHuman) -> MessageAI:
        self._append_human(human_message)
        self._build_messages()
        response = MessageAI(content = f"Echo: {human_message.content}")
        self._append_ai(response)
        return response


def make_agent(policy = None, max_size = 10, prompt_manager = None):
    config = ModelConfig(model_name = "qwen3:1.7b")
    return EchoAgent(
        model = ModelFoundation(config = config),
        prompt_manager = prompt_manager or PromptManager(),
        context_window_policy = policy or KeepAllPolicy(),
        max_context_window_size = max_size,
    )


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

        class CapturingAgent(Agent):
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
            context_window_policy = KeepAllPolicy(),
            max_context_window_size = 10,
        )
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
