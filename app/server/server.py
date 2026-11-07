import json
import asyncio
import logging
import pathlib
import secrets
import subprocess
from pydantic import ValidationError
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from app.server.config import Config
from app.server.requests import SignInRequest
from app.server.builders import build_database
from app.intelligence.tracing import TraceEvent
from app.server.security import SecurityContext
from app.server.chat_sessions import ChatSession
from app.server.builders import build_deep_agent
from app.server.builders import install_security
from app.intelligence.messages import MessageBase
from app.intelligence.messages import MessageHuman
from app.server.security import AuthorizationError
from app.server.security import IdentityEntityType
from app.intelligence.tracing import TraceEventType
from app.intelligence.tracing import TracingService
from app.server.requests import CreateEntityRequest
from app.server.security import AuthenticationError
from app.intelligence.sandbox import SandboxPoolBase
from app.server.security import IdentityAccessAction
from app.server.security import IdentityAccessService
from app.intelligence.sandbox import SandboxPoolDocker
from app.server.security import format_entity_type_vrn
from app.server.security import IdentityAccessStoreSql
from app.server.chat_sessions import ChatSessionStoreSql
from app.intelligence.sandbox import SandboxPoolInMemory
from app.server.security import IdentityAccessRoleSession
from app.server.config_environment import ConfigEnvironment
from app.server.security import AuthenticationPasswordHasher
from app.server.security import format_chat_session_collection_vrn

STATIC_DIR = pathlib.Path(__file__).parent / "static"
POLL_INTERVAL_SECONDS = 0.05
SANDBOX_POOL_SIZE = 10
SESSION_COOKIE = "vela47_session"
AGENT_RESOURCE = "vrn:agent::deep-agent"
TITLE_CHARS = 60

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


def _token_secret(config: Config) -> str:
    """The key that signs session tokens. PROD always has one — Config refuses to start
    without it. In DEV it is optional, and a missing one is generated fresh, which signs
    everyone out on every restart: harmless on a developer's machine, and never a
    fallback to a fixed key anyone could read here."""
    if config.token_secret is not None:
        return config.token_secret.get_secret_value()

    logger.warning(
        "VELA47_TOKEN_SECRET is not set — generating a signing key for this run, so every "
        "session ends when the server restarts."
    )
    return secrets.token_urlsafe(48)


def _bootstrap_admin(identity_access_service: IdentityAccessService, config: Config) -> None:
    """Creates the first admin from the configuration — the environment in DEV, the
    application secret in PROD. Accounts can only be created by an admin, so someone has
    to exist first. Once the database holds that admin this does nothing, so the
    credentials can be dropped from the configuration after the first start."""
    if config.admin_username is None or config.admin_password is None:
        logger.warning(
            "No admin credentials are configured, so no admin is bootstrapped on this start."
        )
        return

    if identity_access_service.find_entity(config.admin_username) is None:
        identity_access_service.create_entity(
            IdentityEntityType.ADMIN,
            config.admin_username,
            config.admin_password.get_secret_value()
        )
        logger.warning("Admin '%s' created from the configuration.", config.admin_username.strip().lower())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Everything with a lifetime longer than a request is set up here, once, in the
    order each piece needs the previous one: configuration, then the database it
    describes, then security on top of that database, then the sandbox containers.
    Starting a container costs far more than a subagent's whole turn, and the database is
    the only record of who exists, so neither could be built per request.

    Configuration and the database start on worker threads — in PROD the first reads
    Secrets Manager and the second creates the schema on RDS — and anything missing or
    malformed fails the start rather than the first request that needs it."""
    config = await asyncio.to_thread(Config.from_environment)
    app.state.config = config

    database = build_database(config)
    await asyncio.to_thread(database.start)
    app.state.database = database
    app.state.chat_session_store = ChatSessionStoreSql(database)
    logger.warning(
        "Database ready: %s in %s mode", database.database_type.value, config.environment.value
    )

    install_security(
        app.state, IdentityAccessStoreSql(database), AuthenticationPasswordHasher(), _token_secret(config)
    )
    _bootstrap_admin(app.state.identity_access_service, config)

    pool = _build_sandbox_pool()
    await asyncio.to_thread(pool.start)
    app.state.sandbox_pool = pool
    logger.warning("Sandbox ready: %s slots in %s", pool.available, type(pool).__name__)

    try:
        yield
    finally:
        await asyncio.to_thread(pool.shutdown)
        logger.warning("Sandbox torn down.")
        await asyncio.to_thread(database.shutdown)
        logger.warning("Database closed.")


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


def _caller(request: Request) -> IdentityAccessRoleSession:
    """The verified role session of whoever sent the request. Needed before authorizing
    anything whose resource names the caller — its own list of conversations — because
    that resource cannot be written down until the caller is known."""
    return request.app.state.authentication_service.verify(request.cookies.get(SESSION_COOKIE))


def _find_chat_session(request: Request, session_id: str) -> ChatSession:
    chat_session = request.app.state.chat_session_store.get_session(session_id)
    if chat_session is None:
        raise HTTPException(status_code = 404, detail = "No such conversation.")
    return chat_session


def _summarize(chat_session: ChatSession) -> dict[str, Any]:
    return {
        "id": chat_session.id,
        "title": chat_session.title,
        "created_at": chat_session.created_at.isoformat(),
        "updated_at": chat_session.updated_at.isoformat(),
        "message_count": len(chat_session.messages)
    }


def _title_for(message: str) -> str:
    """A conversation is named after its first message, flattened onto one line and cut
    short — enough to recognise it in a list, which is all a title is for."""
    flattened = " ".join(message.split()) or "New chat"
    if len(flattened) <= TITLE_CHARS:
        return flattened
    return flattened[:TITLE_CHARS - 1].rstrip() + "…"


def _remember(chat_session: ChatSession, is_new: bool, turn: list[MessageBase]) -> None:
    """Makes one finished exchange durable. A new conversation is written only now,
    together with its first exchange, so a run that fails leaves no empty conversation
    behind; an existing one has the exchange appended."""
    store = app.state.chat_session_store
    if is_new:
        store.create_session(chat_session.model_copy(
            update = {"messages": turn, "updated_at": datetime.now(timezone.utc)}
        ))
    else:
        store.append_messages(chat_session.id, turn)


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


async def _run(message: str, chat_session: ChatSession, is_new: bool) -> AsyncIterator[str]:
    """Streams one exchange. The first frame names the conversation, so the browser
    knows which one a new chat became before any of the answer arrives; the agent is
    built fresh and refilled from the stored conversation, and the exchange is stored
    only once the answer is complete."""
    yield _frame("session", {"id": chat_session.id, "title": chat_session.title, "new": is_new})

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[TraceEvent] = asyncio.Queue()
    tracing_service = TracingService()
    tracing_service.subscribe(
        lambda event: loop.call_soon_threadsafe(queue.put_nowait, event)
    )

    agent = build_deep_agent(tracing_service, app.state.sandbox_pool)
    agent.restore(chat_session.messages)
    human_message = MessageHuman(content = message)
    work = asyncio.create_task(asyncio.to_thread(agent.execute, human_message))

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
        await asyncio.to_thread(_remember, chat_session, is_new, [human_message, response])
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


@app.get("/api/sessions")
def list_chat_sessions(request: Request) -> list[dict[str, Any]]:
    caller = _caller(request)
    _authorize(
        request, IdentityAccessAction.SESSION_LIST, format_chat_session_collection_vrn(caller.entity_id)
    )
    return [
        _summarize(current_session)
        for current_session in request.app.state.chat_session_store.list_sessions(caller.entity_id)
    ]


@app.get("/api/sessions/{session_id}")
def read_chat_session(session_id: str, request: Request) -> dict[str, Any]:
    _caller(request)
    chat_session = _find_chat_session(request, session_id)
    _authorize(request, IdentityAccessAction.SESSION_READ, chat_session.vrn)

    return {
        **_summarize(chat_session),
        "messages": [
            {
                "role": current_message.type.value,
                "content": current_message.content
                if isinstance(current_message.content, str)
                else str(current_message.content)
            }
            for current_message in chat_session.messages
        ]
    }


@app.delete("/api/sessions/{session_id}")
def delete_chat_session(session_id: str, request: Request) -> Response:
    _caller(request)
    chat_session = _find_chat_session(request, session_id)
    _authorize(request, IdentityAccessAction.SESSION_DELETE, chat_session.vrn)
    request.app.state.chat_session_store.delete_session(session_id)
    return Response(status_code = 204)


@app.get("/api/chat/stream")
def chat_stream(request: Request, message: str = Query(min_length = 1),
    session_id: Optional[str] = Query(default = None)) -> StreamingResponse:
    caller = _authorize(request, IdentityAccessAction.AGENT_RUN, AGENT_RESOURCE)

    if session_id is None:
        _authorize(
            request,
            IdentityAccessAction.SESSION_CREATE,
            format_chat_session_collection_vrn(caller.entity_id)
        )
        chat_session = ChatSession(owner_id = caller.entity_id, title = _title_for(message))
    else:
        chat_session = _find_chat_session(request, session_id)
        _authorize(request, IdentityAccessAction.SESSION_WRITE, chat_session.vrn)

    return StreamingResponse(
        _run(message, chat_session, session_id is None),
        media_type = "text/event-stream",
        headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
