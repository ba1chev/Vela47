from app.server.security import SecurityContext
from app.server.security import AuthorizationError
from app.server.security import SecurityServiceBase


class SecurityPipeline:
    """Runs a fixed sequence of security services over one request, threading one
    SecurityContext through them: the security counterpart of OperationPipeline, just as
    ignorant of what each stage does.

    It fails closed twice: a service rejects by raising, and once every service has run,
    anything short of an explicit ALLOW is a denial, so a pipeline built without an
    authorization stage denies everything. Services that need the identity directory are
    given it at construction."""

    def __init__(self, security_services: list[SecurityServiceBase]) -> None:
        self._security_services: list[SecurityServiceBase] = list(security_services)

    def run(self, context: SecurityContext) -> SecurityContext:
        for current_service in self._security_services:
            current_service.execute(context)

        if not context.allowed:
            raise AuthorizationError(
                f"Nothing allowed '{context.action.value}' on '{context.resource}', "
                f"so it is denied."
            )
        return context

    def __len__(self) -> int:
        return len(self._security_services)
