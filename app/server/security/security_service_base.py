from abc import ABC, abstractmethod

from app.server.security.security_context import SecurityContext
from app.server.security.security_service_type import SecurityServiceType


class SecurityServiceBase(ABC):
    """Abstract base for every stage of a SecurityPipeline. Services communicate only
    through the SecurityContext they are handed — each reads what earlier stages vouched
    for and writes the one field it owns — which is why execute() returns nothing,
    exactly as with OperationLayerBase.

    Where an operation layer records a failure and lets the pipeline carry on, a security
    service that cannot vouch for a request raises. Security is the one place where
    continuing past a failed stage is never the right default, and an exception is what
    guarantees that no later stage ever runs on a context an earlier one rejected."""

    @property
    @abstractmethod
    def security_type(self) -> SecurityServiceType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def execute(self, context: SecurityContext) -> None:
        raise NotImplementedError("Must be implemented")
