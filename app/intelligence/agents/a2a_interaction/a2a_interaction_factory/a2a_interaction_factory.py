from typing import Any

from app.intelligence.agents import A2AInteractionType
from app.intelligence.agents import A2AInteractionBase
from app.intelligence.agents import A2A_INTERACTION_REGISTRY
from app.intelligence.agents import A2AInteractionFactoryBase


class A2AInteractionFactory(A2AInteractionFactoryBase):
    """Concrete factory that maps each A2AInteractionType to its A2AInteractionBase
    subclass and forwards the keyword arguments to it. Every call builds a new
    interaction, which holds no agent yet.

    Registry reference:
      HOST   -> A2AInteractionHost()
      DOCKER -> A2AInteractionDocker(left_container=<name>, right_container=<name>)"""

    def create(self, type: A2AInteractionType, **kwargs: Any) -> A2AInteractionBase:
        cls = A2A_INTERACTION_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No interaction class registered for type '{type}'. "
                f"Known types: {list(A2A_INTERACTION_REGISTRY)}"
            )

        return cls(**kwargs)
