from app.messages.message_system import MessageSystem
from app.agents.prompts.prompt_manager import PromptManager


class TestPromptManager:
    def test_starts_empty_when_registry_empty(self):
        pm = PromptManager()
        assert len(pm) == 0

    def test_register_and_get(self):
        pm = PromptManager()
        pm.register("persona", "You are helpful.")
        assert pm.get("persona") == "You are helpful."

    def test_get_unknown_returns_none(self):
        pm = PromptManager()
        assert pm.get("nonexistent") is None

    def test_remove(self):
        pm = PromptManager()
        pm.register("x", "text")
        pm.remove("x")
        assert pm.get("x") is None
        assert len(pm) == 0

    def test_remove_nonexistent_is_noop(self):
        pm = PromptManager()
        pm.remove("ghost")

    def test_contains(self):
        pm = PromptManager()
        pm.register("key", "value")
        assert "key" in pm
        assert "other" not in pm

    def test_build_system_messages_returns_message_system(self):
        pm = PromptManager()
        pm.register("a", "First instruction.")
        pm.register("b", "Second instruction.")
        msgs = pm.build_system_messages()
        assert len(msgs) == 2
        assert all(isinstance(m, MessageSystem) for m in msgs)

    def test_build_system_messages_content(self):
        pm = PromptManager()
        pm.register("p", "Be helpful.")
        msgs = pm.build_system_messages()
        assert msgs[0].content == "Be helpful."

    def test_build_system_messages_empty(self):
        pm = PromptManager()
        assert pm.build_system_messages() == []

    def test_overwrite_existing_key(self):
        pm = PromptManager()
        pm.register("k", "old")
        pm.register("k", "new")
        assert pm.get("k") == "new"
        assert len(pm) == 1
