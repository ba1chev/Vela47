import re

from app.intelligence.security import SecurityPrompt
from app.intelligence.security import SecurityPromptType


class SecurityPromptJailbreaking(SecurityPrompt):
    """Looks in the user's own message for an attempt to talk the model out of its rules:
    a persona without limits, a mode that switches the rules off, a demand to drop its
    guidelines or show its system prompt, or chat-template tokens that open a turn of
    another role.

    It reads only what the user wrote, so its own signatures are about the model being
    addressed ("your rules", "you are now"); in a fetched page the same words are more
    often someone writing about chatbots, which is why injection does not use them. An
    ordinary question about developer mode or system prompts is not a match."""

    PERSONA_OVERRIDE = re.compile(
        r"\b(?:you\s+are|you're|act\s+as|acting\s+as|pretend\s+(?:to\s+be|you\s+are)|role-?play\s+as"
        r"|from\s+now\s+on,?\s+you(?:'re|\s+are|\s+will\s+be)?)[^.\n]{0,40}?"
        r"(?:\b(?-i:DAN)\b|\b(?:jailbroken|unrestricted|unfiltered|uncensored|amoral|unaligned)\b"
        r"|\ban?\s+(?:ai|assistant|model|chatbot)\s+(?:with\s+no|without(?:\s+any)?|that\s+has\s+no)\s+"
        r"(?:rules|restrictions|limits|filters|guidelines)\b)",
        re.IGNORECASE
    )
    MODE_SWITCH = re.compile(
        r"\byou(?:\s+are|'re|\s+will\s+be)\s+(?:now\s+)?(?:in\s+|running\s+in\s+)?"
        r"(?:developer|god|jailbreak|unrestricted|unfiltered|sudo|(?-i:DAN))\s+mode\b"
        r"|\b(?:enable|activate|enter|switch\s+(?:on|to))\s+(?:the\s+)?"
        r"(?:god|jailbreak|unrestricted|unfiltered|(?-i:DAN))\s+mode\b",
        re.IGNORECASE
    )
    RULE_NEGATION = re.compile(
        r"\b(?:ignore|bypass|disable|turn\s+off|forget|drop|override|break|abandon)\s+(?:all\s+(?:of\s+)?)?your\s+"
        r"(?:safety|guidelines|guardrails|restrictions|filters|rules|programming|training|polic(?:y|ies)|principles"
        r"|ethics|limitations|values)\b"
        r"|\byou\s+(?:have|are\s+under|are\s+bound\s+by|follow)\s+no\s+"
        r"(?:rules|restrictions|limits|limitations|filters|guidelines|ethics|morals)\b"
        r"|\byou\s+are\s+(?:now\s+)?(?:free|freed|released|liberated)\s+(?:of|from)\b[^.\n]{0,25}?"
        r"\b(?:rules|restrictions|limits|guidelines|filters|constraints|policies)\b"
        r"|\bwithout\s+(?:any\s+(?:of\s+)?)?your\s+(?:safety|guidelines|guardrails|restrictions|filters|rules|limitations)\b",
        re.IGNORECASE
    )

    @property
    def prompt_type(self) -> SecurityPromptType:
        return SecurityPromptType.JAILBREAKING

    @property
    def signatures(self) -> dict[str, re.Pattern]:
        return {
            "override_instructions": self.OVERRIDE_INSTRUCTIONS,
            "system_impersonation": self.SYSTEM_IMPERSONATION,
            "prompt_extraction": self.PROMPT_EXTRACTION,
            "role_tokens": self.ROLE_TOKENS,
            "persona_override": self.PERSONA_OVERRIDE,
            "mode_switch": self.MODE_SWITCH,
            "rule_negation": self.RULE_NEGATION
        }
