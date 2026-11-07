from typing import Any
from fastapi import APIRouter, HTTPException, Request, Response

from app.server.routes import caller
from app.server.routes import authorize
from app.server.chat_sessions import ChatSession
from app.server.security import IdentityAccessAction
from app.server.security import format_chat_session_collection_vrn

session_router = APIRouter(prefix = "/api/sessions")


def find_chat_session(request: Request, session_id: str) -> ChatSession:
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


@session_router.get("")
def list_chat_sessions(request: Request) -> list[dict[str, Any]]:
    owner = caller(request)
    authorize(
        request, IdentityAccessAction.SESSION_LIST, format_chat_session_collection_vrn(owner.entity_id)
    )
    return [
        _summarize(current_session)
        for current_session in request.app.state.chat_session_store.list_sessions(owner.entity_id)
    ]


@session_router.get("/{session_id}")
def read_chat_session(session_id: str, request: Request) -> dict[str, Any]:
    caller(request)
    chat_session = find_chat_session(request, session_id)
    authorize(request, IdentityAccessAction.SESSION_READ, chat_session.vrn)

    return {
        **_summarize(chat_session),
        "messages": [
            {
                "role": current_message.type.value,
                "agent": current_message.name,
                "sources": current_message.response_metadata.get("sources", []),
                "content": current_message.content
                if isinstance(current_message.content, str)
                else str(current_message.content)
            }
            for current_message in chat_session.messages
        ]
    }


@session_router.delete("/{session_id}")
def delete_chat_session(session_id: str, request: Request) -> Response:
    caller(request)
    chat_session = find_chat_session(request, session_id)
    authorize(request, IdentityAccessAction.SESSION_DELETE, chat_session.vrn)
    request.app.state.chat_session_store.delete_session(session_id)
    return Response(status_code = 204)
