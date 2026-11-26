from typing import Any

from app.intelligence.security import SecurityBase
from app.intelligence.security import SecurityType
from app.intelligence.security import SECURITY_REGISTRY
from app.intelligence.security import SecurityPromptType
from app.intelligence.security import SecurityFactoryBase


class SecurityFactory(SecurityFactoryBase):
    """Concrete factory that picks the factory of a SecurityType's family through
    SECURITY_REGISTRY and lets it build the detector of the threat. A threat of another
    family is not in that factory's registry, so the mismatch is reported by the family
    factory's ValueError.

    Registry reference:
      PROMPT -> SecurityPromptFactory().create(<SecurityPromptType>)"""

    def create(self, type: SecurityType, threat: SecurityPromptType, **kwargs: Any) -> SecurityBase:
        factory = SECURITY_REGISTRY.get(type)

        if factory is None:
            raise ValueError(
                f"No security factory registered for type '{type}'. "
                f"Known types: {list(SECURITY_REGISTRY)}"
            )

        return factory().create(threat, **kwargs)
