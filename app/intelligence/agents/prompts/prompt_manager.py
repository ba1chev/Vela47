from typing import Optional

from app.intelligence.messages.message_system import MessageSystem
from app.intelligence.agents.prompts.prompt_registry import PROMPT_REGISTRY


class PromptManager:
    """Manages named prompt strings and exposes them as MessageSystem entries
    ready to prepend to the context window before every inference call. Prompts
    are registered by name so concrete agents can compose multiple instructions —
    a persona prompt, a tool-use policy, a format constraint — without hard-coding
    them in the agent class. The registry is pre-populated from PROMPT_REGISTRY
    at construction time; additional prompts can be registered at runtime."""

    def __init__(self) -> None:
        self._prompts: dict[str, str] = dict(PROMPT_REGISTRY)

    def register(self, name: str, text: str) -> None:
        self._prompts[name] = text

    def get(self, name: str) -> Optional[str]:
        return self._prompts.get(name)

    def remove(self, name: str) -> None:
        self._prompts.pop(name, None)

    def build_system_messages(self) -> list[MessageSystem]:
        """Returns every registered prompt as an ordered list of MessageSystem
        entries, preserving registration order. Prepend the result to the
        context window messages before calling the model."""
        return [MessageSystem(content = text) for text in self._prompts.values()]

    def __len__(self) -> int:
        return len(self._prompts)

    def __contains__(self, name: str) -> bool:
        return name in self._prompts
