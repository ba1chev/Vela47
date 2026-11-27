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
from app.intelligence.tracing import TracingService
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
    flattened = " ".join(message.split()) or "New chat"
    if len(flattened) <= TITLE_CHARS:
        return flattened
    return flattened[:TITLE_CHARS - 1].rstrip() + "…"


def _searchable_entries(request: Request, owner_id: str) -> list[VectorDbMemoryEntry]:
    try:
        authorize(request, IdentityAccessAction.KNOWLEDGE_SEARCH, format_knowledge_collection_vrn(owner_id))
    except AuthorizationError:
        return []
    return request.app.state.knowledge_store.load_entries(owner_id)


@chat_router.get("/stream")
def chat_stream(request: Request, message: str = Query(min_length = 1),
    session_id: Optional[str] = Query(default = None),
    agent: ChatAgentType = Query(default = ChatAgentType.DEEP)) -> StreamingResponse:
    tracing_service = TracingService()
    with tracing_service.step("Request", "server", {"agent": agent.value, "session_id": session_id}) as span:
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
        tracing_service.record("Conversation", "db", {
            "detail": "a new conversation" if session_id is None else f"{len(chat_session.messages)} earlier messages loaded",
            "conversation": chat_session.id,
            "messages": len(chat_session.messages),
            "new": session_id is None
        })

        state = request.app.state
        if agent is ChatAgentType.RAG:
            authorize(request, IdentityAccessAction.KNOWLEDGE_SEARCH, format_knowledge_collection_vrn(owner.entity_id))
            entries = state.knowledge_store.load_entries(owner.entity_id)
            build_agent = lambda tracer: build_rag_agent(tracer, entries, state.model_client)
        else:
            entries = _searchable_entries(request, owner.entity_id)
            build_agent = lambda tracer: build_deep_agent(
                tracer, state.sandbox_pool, state.web_fetcher, state.web_search, entries, state.model_client
            )
        tracing_service.record("Documents", "db", {
            "detail": f"{len(entries)} chunks of {len({current.metadata.source.document_id for current in entries if current.metadata})} document(s) loaded",
            "chunks": len(entries)
        })
        span["detail"] = f"{owner.role_type.value} {owner.entity_type.value}, {agent.value} agent"

    return StreamingResponse(
        stream_chat(state, message, chat_session, session_id is None, build_agent, agent.value, tracing_service = tracing_service),
        media_type = "text/event-stream",
        headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
