from typing import Any

from app.intelligence.security import SecurityPrompt
from app.intelligence.security import SecurityPromptType
from app.intelligence.security import SECURITY_PROMPT_REGISTRY
from app.intelligence.security import SecurityPromptFactoryBase


class SecurityPromptFactory(SecurityPromptFactoryBase):
    """Concrete factory that maps each SecurityPromptType to its SecurityPrompt subclass
    through SECURITY_PROMPT_REGISTRY and forwards the keyword arguments to it. A detector
    keeps nothing between texts, so one built here can serve every run.

    Registry reference:
      INJECTION    -> SecurityPromptInjection()
      JAILBREAKING -> SecurityPromptJailbreaking()
      POISONING    -> SecurityPromptPoisoning()"""

    def create(self, type: SecurityPromptType, **kwargs: Any) -> SecurityPrompt:
        cls = SECURITY_PROMPT_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No prompt detector class registered for type '{type}'. "
                f"Known types: {list(SECURITY_PROMPT_REGISTRY)}"
            )

        return cls(**kwargs)
