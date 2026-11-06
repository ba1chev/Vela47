from app.server.security.security_context import SecurityContext
from app.server.security.security_service_base import SecurityServiceBase
from app.server.security.authorization.authorization_error import AuthorizationError


class SecurityPipeline:
    """Runs a fixed sequence of security services over one request, in the order given,
    threading a single SecurityContext through all of them — the security counterpart of
    OperationPipeline, and just as deliberately ignorant of what each stage does.

    It fails closed, twice over. A service rejects by raising, which stops the run before
    any later stage sees the context. And once every service has run, anything short of
    an explicit ALLOW is a denial. That second check is what makes a misassembled
    pipeline safe: one built without an authorization stage denies every request rather
    than waving through anyone who merely proved who they are.

    The identity directory is not held here. The services that need it are given it at
    construction, so the pipeline stays a plain runner that never needs to change when a
    stage is added."""

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
