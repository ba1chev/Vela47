from typing import Optional
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from app.server.routes import authorize
from app.server.routes import stream_chat
from app.server.routes import ChatAgentType
from app.server.routes import find_chat_session
from app.server.builders import build_rag_agent
from app.server.builders import build_deep_agent
from app.server.chat_sessions import ChatSession
from app.server.security import AuthorizationError
from app.server.security import IdentityAccessAction
from app.intelligence.memory import VectorDbMemoryEntry
from app.server.security import format_knowledge_collection_vrn
from app.server.security import format_chat_session_collection_vrn

AGENT_RESOURCES = {
    ChatAgentType.DEEP: "vrn:agent::deep-agent",
    ChatAgentType.RAG: "vrn:agent::rag-agent"
}
TITLE_CHARS = 60

chat_router = APIRouter(prefix = "/api/chat")


def _title_for(message: str) -> str:
    """A conversation is named after its first message, flattened onto one line and cut
    short — enough to recognise it in a list, which is all a title is for."""
    flattened = " ".join(message.split()) or "New chat"
    if len(flattened) <= TITLE_CHARS:
        return flattened
    return flattened[:TITLE_CHARS - 1].rstrip() + "…"


def _searchable_entries(request: Request, owner_id: str) -> list[VectorDbMemoryEntry]:
    """The documents the deep agent's research steps may search: the caller's own, when
    its role allows searching them, and none otherwise. Unlike the RAG agent, the deep
    agent has other work to do without them, so a caller without the permission still
    gets an agent — just one whose document search finds nothing."""
    try:
        authorize(request, IdentityAccessAction.KNOWLEDGE_SEARCH, format_knowledge_collection_vrn(owner_id))
    except AuthorizationError:
        return []
    return request.app.state.knowledge_store.load_entries(owner_id)


@chat_router.get("/stream")
def chat_stream(request: Request, message: str = Query(min_length = 1),
    session_id: Optional[str] = Query(default = None),
    agent: ChatAgentType = Query(default = ChatAgentType.DEEP)) -> StreamingResponse:
    owner = authorize(request, IdentityAccessAction.AGENT_RUN, AGENT_RESOURCES[agent])

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

    state = request.app.state
    if agent is ChatAgentType.RAG:
        authorize(request, IdentityAccessAction.KNOWLEDGE_SEARCH, format_knowledge_collection_vrn(owner.entity_id))
        entries = state.knowledge_store.load_entries(owner.entity_id)
        build_agent = lambda tracing_service: build_rag_agent(tracing_service, entries, state.config.environment)
    else:
        entries = _searchable_entries(request, owner.entity_id)
        build_agent = lambda tracing_service: build_deep_agent(
            tracing_service, state.sandbox_pool, state.web_fetcher, entries, state.config.environment
        )

    return StreamingResponse(
        stream_chat(state, message, chat_session, session_id is None, build_agent, agent.value),
        media_type = "text/event-stream",
        headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
