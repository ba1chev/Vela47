from enum import Enum


class A2AInteractionType(str, Enum):
    """Enumerates how the two agents of an interaction reach each other. HOST is two
    agents in the same process, a message handed from one to the other directly. DOCKER
    is two subagents whose sandboxes are containers on the same host, a message carried
    from one container to the other over a network of their own."""

    HOST = "host"
    DOCKER = "docker"
