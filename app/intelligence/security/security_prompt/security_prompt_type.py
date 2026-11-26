from enum import Enum


class SecurityPromptType(str, Enum):
    """Enumerates the prompt threats, told apart by where the text comes from rather than
    by what it says, since the same sentence can be any of them.

    JAILBREAKING is in the user's own message and works against the model's rules.
    INJECTION arrives during a run in what a tool brought back: a page, a search snippet,
    test output, another worker's answer. POISONING was stored before the run, in a
    document or an earlier turn, and is read again by every run that retrieves it."""

    INJECTION = "injection"
    JAILBREAKING = "jailbreaking"
    POISONING = "poisoning"
