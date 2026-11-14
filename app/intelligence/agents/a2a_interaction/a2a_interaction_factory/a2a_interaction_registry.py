from app.intelligence.agents import A2AInteractionType
from app.intelligence.agents import A2AInteractionBase
from app.intelligence.agents import A2AInteractionHost
from app.intelligence.agents import A2AInteractionDocker


A2A_INTERACTION_REGISTRY: dict[A2AInteractionType, type[A2AInteractionBase]] = {
    A2AInteractionType.HOST: A2AInteractionHost,
    A2AInteractionType.DOCKER: A2AInteractionDocker
}
