from typing import Any
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Response

from app.server.routes import caller
from app.server.routes import SESSION_COOKIE
from app.server.requests import SignInRequest
from app.server.security import IdentityAccessRoleSession
from app.server.config_environment import ConfigEnvironment

auth_router = APIRouter(prefix = "/api/auth")


def _describe(request: Request, session: IdentityAccessRoleSession) -> dict[str, Any]:
    entity = request.app.state.identity_access_service.resolve_entity(session)
    return {
        "entity_id": session.entity_id,
        "entity_type": session.entity_type.value,
        "name": entity.name if entity is not None else None,
        "role": session.role_type.value,
        "expires_at": session.expires_at.isoformat()
    }


def _open_session(request: Request, response: Response,
    session: IdentityAccessRoleSession) -> dict[str, Any]:
    """Hands a freshly assumed role session to the browser as a cookie, which is what
    lets EventSource carry it — EventSource cannot set an Authorization header. HttpOnly
    keeps page scripts from ever reading the token, and SameSite=Strict keeps other
    sites from making the browser send it. Secure is always on in PROD, where TLS ends at
    the load balancer and the request reaching the server is plain HTTP even though the
    browser's was not; in DEV it follows the scheme, staying off on plain-HTTP localhost,
    where some browsers refuse to store a Secure cookie at all."""
    response.set_cookie(
        SESSION_COOKIE,
        request.app.state.authentication_service.issue_token(session),
        max_age = max(0, int((session.expires_at - datetime.now(timezone.utc)).total_seconds())),
        httponly = True,
        samesite = "strict",
        secure = (
            request.app.state.config.environment is ConfigEnvironment.PROD
            or request.url.scheme == "https"
        ),
        path = "/"
    )
    return _describe(request, session)


@auth_router.post("/guest")
def sign_in_guest(request: Request, response: Response) -> dict[str, Any]:
    session = request.app.state.authentication_service.sign_in_guest()
    return _open_session(request, response, session)


@auth_router.post("/login")
def sign_in(body: SignInRequest, request: Request, response: Response) -> dict[str, Any]:
    session = request.app.state.authentication_service.sign_in(body.name, body.password, body.role)
    return _open_session(request, response, session)


@auth_router.post("/logout")
def sign_out() -> Response:
    response = Response(status_code = 204)
    response.delete_cookie(SESSION_COOKIE, path = "/", httponly = True, samesite = "strict")
    return response


@auth_router.get("/me")
def who_am_i(request: Request) -> dict[str, Any]:
    return _describe(request, caller(request))
