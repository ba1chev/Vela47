from fastapi import Request

from app.server.security import SecurityContext
from app.server.security import IdentityAccessAction
from app.server.security import IdentityAccessRoleSession

SESSION_COOKIE = "vela47_session"


def authorize(request: Request, action: IdentityAccessAction,
    resource: str) -> IdentityAccessRoleSession:
    """Runs the security pipeline for one request. Every protected endpoint calls this
    before it does any work, so a rejected request never leaves anything half-done."""
    context = request.app.state.security_pipeline.run(SecurityContext(
        token = request.cookies.get(SESSION_COOKIE),
        action = action,
        resource = resource
    ))
    return context.session


def caller(request: Request) -> IdentityAccessRoleSession:
    """The verified role session of whoever sent the request. Needed before authorizing
    anything whose resource names the caller — its own list of conversations — because
    that resource cannot be written down until the caller is known."""
    return request.app.state.authentication_service.verify(request.cookies.get(SESSION_COOKIE))
