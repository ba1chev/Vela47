from app.intelligence.security import SecurityPrompt
from app.intelligence.security import SecurityPromptType
from app.intelligence.security import SecurityPromptInjection
from app.intelligence.security import SecurityPromptPoisoning
from app.intelligence.security import SecurityPromptJailbreaking


SECURITY_PROMPT_REGISTRY: dict[SecurityPromptType, type[SecurityPrompt]] = {
    SecurityPromptType.INJECTION: SecurityPromptInjection,
    SecurityPromptType.JAILBREAKING: SecurityPromptJailbreaking,
    SecurityPromptType.POISONING: SecurityPromptPoisoning
}
