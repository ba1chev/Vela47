from typing import Optional
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from app.server.routes import authorize
from app.server.routes import stream_chat
from app.server.routes import find_chat_session
from app.server.chat_sessions import ChatSession
from app.server.security import IdentityAccessAction
from app.server.security import format_chat_session_collection_vrn

AGENT_RESOURCE = "vrn:agent::deep-agent"
TITLE_CHARS = 60

chat_router = APIRouter(prefix = "/api/chat")


def _title_for(message: str) -> str:
    """A conversation is named after its first message, flattened onto one line and cut
    short — enough to recognise it in a list, which is all a title is for."""
    flattened = " ".join(message.split()) or "New chat"
    if len(flattened) <= TITLE_CHARS:
        return flattened
    return flattened[:TITLE_CHARS - 1].rstrip() + "…"


@chat_router.get("/stream")
def chat_stream(request: Request, message: str = Query(min_length = 1),
    session_id: Optional[str] = Query(default = None)) -> StreamingResponse:
    owner = authorize(request, IdentityAccessAction.AGENT_RUN, AGENT_RESOURCE)

    if session_id is None:
        authorize(
            request,
            IdentityAccessAction.SESSION_CREATE,
            format_chat_session_collection_vrn(owner.entity_id)
        )
        chat_session = ChatSession(owner_id = owner.entity_id, title = _title_for(message))
    else:
        chat_session = find_chat_session(request, session_id)
        authorize(request, IdentityAccessAction.SESSION_WRITE, chat_session.vrn)

    return StreamingResponse(
        stream_chat(request.app.state, message, chat_session, session_id is None),
        media_type = "text/event-stream",
        headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
