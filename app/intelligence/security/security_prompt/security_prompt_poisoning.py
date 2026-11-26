import re

from app.intelligence.security import SecurityPrompt
from app.intelligence.security import SecurityPromptType


class SecurityPromptPoisoning(SecurityPrompt):
    """Looks in stored text, a document chunk or an earlier turn of the conversation, for
    an injection written in advance that waits to be retrieved. It looks for everything
    SecurityPromptInjection does, and besides that for text that argues for its own
    relevance to win a place among the passages, such as asking the reranker, which
    scores from 0 to 10, for a 10.

    Stored text is read again by every run that retrieves it, so one poisoned chunk can
    steer every answer that cites it, long after it was uploaded."""

    RANKING_MANIPULATION = re.compile(
        r"\b(?:this|the\s+following)\s+(?:passage|document|source|text|section|chunk|page)\s+"
        r"(?:is|contains|has|provides)\s+(?:the\s+)?(?:most\s+relevant|highly\s+relevant|(?:only|correct|definitive)\s+answer)\b"
        r"|\b(?:give|assign)\s+(?:this|it|the\s+following)\b[^.\n]{0,20}?\b(?:a\s+)?(?:relevance\s+)?score\s+of\s+(?:10|ten)\b"
        r"|\bscore\s+(?:this|it)\s+(?:a\s+)?(?:10|ten)\b|\brelevance\s+score\b[^.\n]{0,20}?\b(?:10|ten)\b"
        r"|\b(?:always|must)\s+(?:be\s+)?(?:ranked|scored|rated|retrieved|cited)\s+(?:first|highest|above)\b",
        re.IGNORECASE
    )

    @property
    def prompt_type(self) -> SecurityPromptType:
        return SecurityPromptType.POISONING

    @property
    def signatures(self) -> dict[str, re.Pattern]:
        return {
            "override_instructions": self.OVERRIDE_INSTRUCTIONS,
            "system_impersonation": self.SYSTEM_IMPERSONATION,
            "prompt_extraction": self.PROMPT_EXTRACTION,
            "role_tokens": self.ROLE_TOKENS,
            "address_to_ai": self.ADDRESS_TO_AI,
            "pipeline_markers": self.PIPELINE_MARKERS,
            "exfiltration_image": self.EXFILTRATION_IMAGE,
            "ranking_manipulation": self.RANKING_MANIPULATION
        }
