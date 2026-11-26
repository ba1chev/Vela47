import re

from app.intelligence.security import SecurityPrompt
from app.intelligence.security import SecurityPromptType


class SecurityPromptInjection(SecurityPrompt):
    """Looks in what a tool brought back during a run (a page, a search snippet, test
    output, another worker's answer) for text addressed to the model instead of a
    reader: an order to drop its instructions, a message posing as the system or written
    to an AI, chat-template tokens, or a Markdown image whose address waits for what the
    model knows to be filled in, which the browser would then send away.

    Its most telling signature is the frames Vela47's own layers write around tasks,
    reports and sources. Merging trusts a line that starts "Checked by the system", so
    text that imitates those frames tries to pass as the system, and an honest page has
    no reason to contain them."""

    @property
    def prompt_type(self) -> SecurityPromptType:
        return SecurityPromptType.INJECTION

    @property
    def signatures(self) -> dict[str, re.Pattern]:
        return {
            "override_instructions": self.OVERRIDE_INSTRUCTIONS,
            "system_impersonation": self.SYSTEM_IMPERSONATION,
            "prompt_extraction": self.PROMPT_EXTRACTION,
            "role_tokens": self.ROLE_TOKENS,
            "address_to_ai": self.ADDRESS_TO_AI,
            "pipeline_markers": self.PIPELINE_MARKERS,
            "exfiltration_image": self.EXFILTRATION_IMAGE
        }
