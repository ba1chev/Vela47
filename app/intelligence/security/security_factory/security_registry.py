from app.intelligence.security import SecurityType
from app.intelligence.security import SecurityPromptFactory
from app.intelligence.security import SecurityPromptFactoryBase


SECURITY_REGISTRY: dict[SecurityType, type[SecurityPromptFactoryBase]] = {
    SecurityType.PROMPT: SecurityPromptFactory
}
