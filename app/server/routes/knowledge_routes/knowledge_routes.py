import asyncio
import logging
from typing import Any, AsyncIterator, Callable
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, HTTPException, Query, Request, Response

from app.server.routes import caller
from app.server.routes import authorize
from app.server.routes import sse_frame
from app.server.routes import relay_trace
from app.server.routes import trace_queue
from app.server.routes import stored_trace
from app.server.knowledge import KnowledgeDocument
from app.intelligence.tracing import TracingService
from app.server.knowledge import KnowledgeIngestion
from app.server.security import IdentityAccessAction
from app.server.requests import UploadKnowledgeRequest
from app.intelligence.tracing import TracingServiceBase
from app.server.knowledge import KnowledgeIngestionError
from app.server.requests import ImportKnowledgeUrlRequest
from app.server.security import format_knowledge_collection_vrn

knowledge_router = APIRouter(prefix = "/api/knowledge")
logger = logging.getLogger("vela47")


def _describe(document: KnowledgeDocument) -> dict[str, Any]:
    return {
        "id": document.id,
        "title": document.title,
        "size_bytes": document.size_bytes,
        "chunk_count": document.chunk_count,
        "created_at": document.created_at.isoformat()
    }


def _usage(request: Request, owner_id: str) -> dict[str, Any]:
    config = request.app.state.config
    return {
        "used_bytes": request.app.state.knowledge_store.used_bytes(owner_id),
        "max_bytes": config.knowledge_max_owner_bytes,
        "max_file_bytes": config.knowledge_max_file_bytes,
        "max_upload_bytes": config.knowledge_max_upload_bytes
    }


def _ingestion(request: Request, tracing_service: TracingServiceBase) -> KnowledgeIngestion:
    state = request.app.state
    return KnowledgeIngestion(state.config, state.knowledge_store, state.rag_indexer, state.web_fetcher, tracing_service)


def _added(request: Request, owner_id: str, document: KnowledgeDocument,
    tracing_service: TracingServiceBase) -> dict[str, Any]:
    request.app.state.knowledge_store.set_trace(document.id, stored_trace(tracing_service.events()))
    return {"document": _describe(document), "usage": _usage(request, owner_id)}


async def _stream_ingestion(request: Request, owner_id: str, tracing_service: TracingServiceBase,
    ingest: Callable[[KnowledgeIngestion], KnowledgeDocument]) -> AsyncIterator[str]:
    queue = trace_queue(tracing_service)
    work = asyncio.create_task(asyncio.to_thread(ingest, _ingestion(request, tracing_service)))

    async for current_frame in relay_trace(queue, work):
        yield current_frame

    try:
        document = await work
        added = await asyncio.to_thread(_added, request, owner_id, document, tracing_service)
        yield sse_frame("document", added)
    except KnowledgeIngestionError as error:
        yield sse_frame("error", {"status": error.status_code, "detail": error.detail})
    except Exception as error:
        logger.exception("Adding a document failed for %s", owner_id)
        yield sse_frame("error", {"status": 500, "detail": f"{type(error).__name__}: {error}"})


def _authorized(request: Request) -> tuple[str, TracingServiceBase]:
    owner = caller(request)
    tracing_service = TracingService()
    with tracing_service.step("Request", "server") as span:
        authorize(request, IdentityAccessAction.KNOWLEDGE_UPLOAD, format_knowledge_collection_vrn(owner.entity_id))
        span["detail"] = f"{owner.role_type.value} {owner.entity_type.value} adding a document"
    return owner.entity_id, tracing_service


def _add(request: Request, owner_id: str, tracing_service: TracingServiceBase, stream: bool,
    ingest: Callable[[KnowledgeIngestion], KnowledgeDocument]) -> Any:
    if stream:
        return StreamingResponse(
            _stream_ingestion(request, owner_id, tracing_service, ingest),
            status_code = 201,
            media_type = "text/event-stream",
            headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )

    try:
        document = ingest(_ingestion(request, tracing_service))
    except KnowledgeIngestionError as error:
        raise HTTPException(status_code = error.status_code, detail = error.detail) from None
    return _added(request, owner_id, document, tracing_service)


@knowledge_router.get("")
def list_knowledge(request: Request) -> dict[str, Any]:
    owner = caller(request)
    authorize(request, IdentityAccessAction.KNOWLEDGE_LIST, format_knowledge_collection_vrn(owner.entity_id))

    return {
        "documents": [
            _describe(current_document)
            for current_document in request.app.state.knowledge_store.list_documents(owner.entity_id)
        ],
        "usage": _usage(request, owner.entity_id)
    }


@knowledge_router.post("", status_code = 201)
def upload_knowledge(body: UploadKnowledgeRequest, request: Request,
    stream: bool = Query(default = False)) -> Any:
    owner_id, tracing_service = _authorized(request)
    return _add(request, owner_id, tracing_service, stream, lambda ingestion: ingestion.upload(owner_id, body))


@knowledge_router.post("/url", status_code = 201)
def import_knowledge_url(body: ImportKnowledgeUrlRequest, request: Request,
    stream: bool = Query(default = False)) -> Any:
    owner_id, tracing_service = _authorized(request)
    return _add(request, owner_id, tracing_service, stream, lambda ingestion: ingestion.import_url(owner_id, body))


@knowledge_router.get("/{document_id}/trace")
def read_knowledge_trace(document_id: str, request: Request) -> dict[str, Any]:
    caller(request)
    document = request.app.state.knowledge_store.get_document(document_id)
    if document is None:
        raise HTTPException(status_code = 404, detail = "No such document.")

    authorize(request, IdentityAccessAction.KNOWLEDGE_LIST, format_knowledge_collection_vrn(document.owner_id))
    return {"document": _describe(document), "trace": request.app.state.knowledge_store.get_trace(document_id) or []}


@knowledge_router.delete("/{document_id}")
def delete_knowledge(document_id: str, request: Request) -> Response:
    caller(request)
    document = request.app.state.knowledge_store.get_document(document_id)
    if document is None:
        raise HTTPException(status_code = 404, detail = "No such document.")

    authorize(request, IdentityAccessAction.KNOWLEDGE_DELETE, document.vrn)
    request.app.state.knowledge_store.delete_document(document_id)
    return Response(status_code = 204)
