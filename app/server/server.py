import pathlib
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.server.routes import iam_router
from app.server.routes import auth_router
from app.server.routes import chat_router
from app.server.routes import session_router
from app.server.server_lifespan import lifespan
from app.server.security import AuthorizationError
from app.server.security import AuthenticationError

STATIC_DIR = pathlib.Path(__file__).parent / "static"

app = FastAPI(title = "Vela47", lifespan = lifespan)
app.mount("/static", StaticFiles(directory = STATIC_DIR), name = "static")
for current_router in (auth_router, iam_router, session_router, chat_router):
    app.include_router(current_router)


@app.exception_handler(AuthenticationError)
async def on_authentication_error(request: Request, error: AuthenticationError) -> JSONResponse:
    return JSONResponse({"detail": str(error)}, status_code = 401)


@app.exception_handler(AuthorizationError)
async def on_authorization_error(request: Request, error: AuthorizationError) -> JSONResponse:
    return JSONResponse({"detail": str(error)}, status_code = 403)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
