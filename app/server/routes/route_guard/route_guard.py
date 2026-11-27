from fastapi import Request

from app.server.security import SecurityContext
from app.server.security import IdentityAccessAction
from app.server.security import IdentityAccessRoleSession

SESSION_COOKIE = "vela47_session"


def authorize(request: Request, action: IdentityAccessAction,
    resource: str) -> IdentityAccessRoleSession:
    context = request.app.state.security_pipeline.run(SecurityContext(
        token = request.cookies.get(SESSION_COOKIE),
        action = action,
        resource = resource
    ))
    return context.session


def caller(request: Request) -> IdentityAccessRoleSession:
    return request.app.state.authentication_service.verify(request.cookies.get(SESSION_COOKIE))
