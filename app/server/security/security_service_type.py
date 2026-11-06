from enum import Enum


class SecurityServiceType(str, Enum):
    """Enumerates the stages a SecurityPipeline can run. Authentication answers who is
    asking and authorization answers whether they may. Their order is not a convention
    but a dependency: nothing can be permitted to a caller whose identity is not yet
    known."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
