from enum import Enum


class SecurityType(str, Enum):
    """Enumerates the families of threat the intelligence layer watches for. Each value
    maps to the factory of its family in SECURITY_REGISTRY, which builds the detector of
    one threat of that family.

    PROMPT is text written to steer a model rather than to inform it: a jailbreak in the
    user's own message, an injection in what a tool brought back, poisoning in what was
    stored and is read again."""

    PROMPT = "prompt"
