import os
import json
import asyncio
import logging
import pathlib
import secrets
import subprocess
from pydantic import ValidationError
from typing import Any, AsyncIterator
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from app.intelligence.tracing import TraceEvent
from app.intelligence.messages import MessageHuman
from app.intelligence.tracing import TraceEventType
from app.intelligence.tracing import TracingService
from app.intelligence.sandbox import SandboxPoolBase
from app.server.agent_builder import build_deep_agent
from app.intelligence.sandbox import SandboxPoolDocker
from app.server.security_builder import install_security
from app.intelligence.sandbox import SandboxPoolInMemory
from app.server.requests.sign_in_request import SignInRequest
from app.server.security.security_context import SecurityContext
from app.server.requests.create_entity_request import CreateEntityRequest
from app.server.security.authorization.authorization_error import AuthorizationError
from app.server.security.authentication.authentication_error import AuthenticationError
from app.server.security.identity_access.identity_access_vrn import format_entity_type_vrn
from app.server.security.identity_access.identity_access_action import IdentityAccessAction
from app.server.security.identity_access.identity_access_service import IdentityAccessService
from app.server.security.identity_access.identity_access_role_session import IdentityAccessRoleSession
from app.server.security.identity_access.identity_entities.identity_entity_type import IdentityEntityType
from app.server.security.authentication.authentication_password_hasher import AuthenticationPasswordHasher

STATIC_DIR = pathlib.Path(__file__).parent / "static"
POLL_INTERVAL_SECONDS = 0.05
SANDBOX_POOL_SIZE = 10
SESSION_COOKIE = "vela47_session"
AGENT_RESOURCE = "vrn:agent::deep-agent"
TOKEN_SECRET_VARIABLE = "VELA47_TOKEN_SECRET"
ADMIN_USERNAME_VARIABLE = "VELA47_ADMIN_USERNAME"
ADMIN_PASSWORD_VARIABLE = "VELA47_ADMIN_PASSWORD"

logger = logging.getLogger("vela47")


def _docker_is_available() -> bool:
    try:
        return subprocess.run(
            ["docker", "info"], capture_output = True, timeout = 10, check = False
        ).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _build_sandbox_pool() -> SandboxPoolBase:
    """Containers when Docker is reachable, a bare directory when it is not.

    The fallback is loud rather than silent: without containers the local pool
    refuses to run commands at all, so a TEST subagent fails with an explanation
    instead of quietly executing model-written code on the host."""
    if _docker_is_available():
        return SandboxPoolDocker(size = SANDBOX_POOL_SIZE)

    logger.warning(
        "Docker is not reachable — falling back to a local sandbox. Subagents can "
        "write files but cannot run commands."
    )
    return SandboxPoolInMemory(size = SANDBOX_POOL_SIZE)


def _token_secret() -> str:
    """The key that signs session tokens. Taken from the environment when set, so that
    sessions survive a restart; otherwise generated fresh, which signs everyone out on
    every restart. That is an acceptable cost while the store forgets every account on
    restart anyway — and it is never a fallback to a fixed key anyone could read here."""
    secret = os.environ.get(TOKEN_SECRET_VARIABLE)
    if secret:
        return secret

    logger.warning(
        "%s is not set — generating a signing key for this run, so every session ends "
        "when the server restarts.", TOKEN_SECRET_VARIABLE
    )
    return secrets.token_urlsafe(48)


def _bootstrap_admin(identity_access_service: IdentityAccessService) -> None:
    """Creates the first admin from the environment. Accounts can only be created by an
    admin, so someone has to exist before anyone else can. Without the variables the
    server still runs and still serves guests — there is simply nobody who can create
    an account."""
    name = os.environ.get(ADMIN_USERNAME_VARIABLE)
    password = os.environ.get(ADMIN_PASSWORD_VARIABLE)

    if not name or not password:
        logger.warning(
            "%s / %s are not set — there is no admin, so no accounts can be created. "
            "Guests can still use the agent.", ADMIN_USERNAME_VARIABLE, ADMIN_PASSWORD_VARIABLE
        )
        return

    if identity_access_service.find_entity(name) is None:
        identity_access_service.create_entity(IdentityEntityType.ADMIN, name, password)
        logger.warning("Admin '%s' created from the environment.", name.strip().lower())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Containers are started once for the process and torn down on the way out.
    Starting one costs far more than a subagent's whole turn, so paying it per
    request would dominate every run.

    Security is installed first, and also once. The identity store is the only
    record of who exists, so it has to outlive every request, and a missing or
    malformed secret or admin password fails the start rather than the first sign-in."""
    install_security(app.state, AuthenticationPasswordHasher(), _token_secret())
    _bootstrap_admin(app.state.identity_access_service)

    pool = _build_sandbox_pool()
    await asyncio.to_thread(pool.start)
    app.state.sandbox_pool = pool
    logger.warning("Sandbox ready: %s slots in %s", pool.available, type(pool).__name__)

    try:
        yield
    finally:
        await asyncio.to_thread(pool.shutdown)
        logger.warning("Sandbox torn down.")


app = FastAPI(title = "Vela47", lifespan = lifespan)
app.mount("/static", StaticFiles(directory = STATIC_DIR), name = "static")


@app.exception_handler(AuthenticationError)
async def on_authentication_error(request: Request, error: AuthenticationError) -> JSONResponse:
    return JSONResponse({"detail": str(error)}, status_code = 401)


@app.exception_handler(AuthorizationError)
async def on_authorization_error(request: Request, error: AuthorizationError) -> JSONResponse:
    return JSONResponse({"detail": str(error)}, status_code = 403)


def _authorize(request: Request, action: IdentityAccessAction,
    resource: str) -> IdentityAccessRoleSession:
    """Runs the security pipeline for one request. Every protected endpoint calls this
    before it does any work, so a rejected request never leaves anything half-done."""
    context = request.app.state.security_pipeline.run(SecurityContext(
        token = request.cookies.get(SESSION_COOKIE),
        action = action,
        resource = resource
    ))
    return context.session


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
    sites from making the browser send it. Secure follows the scheme the page was served
    over: on, behind HTTPS; off on plain-HTTP localhost, where some browsers refuse to
    store a Secure cookie at all."""
    response.set_cookie(
        SESSION_COOKIE,
        request.app.state.authentication_service.issue_token(session),
        max_age = max(0, int((session.expires_at - datetime.now(timezone.utc)).total_seconds())),
        httponly = True,
        samesite = "strict",
        secure = request.url.scheme == "https",
        path = "/"
    )
    return _describe(request, session)


def _frame(event: str, data: dict[str, Any]) -> str:
    """Formats one Server-Sent Events frame. The blank line terminates the frame —
    without it the browser buffers indefinitely waiting for more of the message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _frame_for(event: TraceEvent) -> str:
    """Answer chunks travel the same internal channel as observations but are content,
    not progress, so they leave as their own SSE event — the browser appends them to
    the reply rather than listing them in the trace."""
    if event.type is TraceEventType.ANSWER_CHUNK:
        return _frame("chunk", {"text": event.payload.get("text", "")})
    return _frame("trace", event.model_dump(mode = "json"))


async def _run(message: str) -> AsyncIterator[str]:
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[TraceEvent] = asyncio.Queue()
    tracing_service = TracingService()
    tracing_service.subscribe(
        lambda event: loop.call_soon_threadsafe(queue.put_nowait, event)
    )

    agent = build_deep_agent(tracing_service, app.state.sandbox_pool)
    work = asyncio.create_task(
        asyncio.to_thread(agent.execute, MessageHuman(content = message))
    )

    while True:
        while not queue.empty():
            yield _frame_for(queue.get_nowait())
        if work.done():
            break
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

    while not queue.empty():
        yield _frame_for(queue.get_nowait())

    try:
        response = await work
        content = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )
        yield _frame("answer", {"content": content})
    except Exception as e:
        yield _frame("error", {"message": f"{type(e).__name__}: {e}"})


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/auth/guest")
def sign_in_guest(request: Request, response: Response) -> dict[str, Any]:
    session = request.app.state.authentication_service.sign_in_guest()
    return _open_session(request, response, session)


@app.post("/api/auth/login")
def sign_in(body: SignInRequest, request: Request, response: Response) -> dict[str, Any]:
    session = request.app.state.authentication_service.sign_in(body.name, body.password, body.role)
    return _open_session(request, response, session)


@app.post("/api/auth/logout")
def sign_out() -> Response:
    response = Response(status_code = 204)
    response.delete_cookie(SESSION_COOKIE, path = "/", httponly = True, samesite = "strict")
    return response


@app.get("/api/auth/me")
def who_am_i(request: Request) -> dict[str, Any]:
    session = request.app.state.authentication_service.verify(request.cookies.get(SESSION_COOKIE))
    return _describe(request, session)


@app.post("/api/iam/entities", status_code = 201)
def create_entity(body: CreateEntityRequest, request: Request) -> dict[str, Any]:
    _authorize(request, IdentityAccessAction.IAM_CREATE_ENTITY, format_entity_type_vrn(body.type))

    try:
        entity = request.app.state.identity_access_service.create_entity(
            body.type, body.name, body.password
        )
    except ValidationError as error:
        raise HTTPException(
            status_code = 400,
            detail = "; ".join(current_error["msg"] for current_error in error.errors())
        ) from None
    except ValueError as error:
        raise HTTPException(status_code = 400, detail = str(error)) from None

    return {"id": entity.id, "type": entity.type.value, "name": entity.name}


@app.get("/api/chat/stream")
async def chat_stream(request: Request, message: str = Query(min_length = 1)) -> StreamingResponse:
    _authorize(request, IdentityAccessAction.AGENT_RUN, AGENT_RESOURCE)

    return StreamingResponse(
        _run(message),
        media_type = "text/event-stream",
        headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
