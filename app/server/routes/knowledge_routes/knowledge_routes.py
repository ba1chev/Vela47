from uuid import uuid4
from typing import Any
from fastapi import APIRouter, HTTPException, Request, Response

from app.server.routes import caller
from app.server.routes import authorize
from app.server.knowledge import KnowledgeDocument
from app.server.security import IdentityAccessAction
from app.server.requests import UploadKnowledgeRequest
from app.server.security import format_knowledge_collection_vrn

knowledge_router = APIRouter(prefix = "/api/knowledge")


def _describe(document: KnowledgeDocument) -> dict[str, Any]:
    return {
        "id": document.id,
        "title": document.title,
        "size_bytes": document.size_bytes,
        "chunk_count": document.chunk_count,
        "created_at": document.created_at.isoformat()
    }


def _usage(request: Request, owner_id: str) -> dict[str, Any]:
    """What the sidebar draws its limit from. Sent with every listing and every upload,
    so the bar moves the moment the storage behind it changes, without a request of its
    own."""
    config = request.app.state.config
    return {
        "used_bytes": request.app.state.knowledge_store.used_bytes(owner_id),
        "max_bytes": config.knowledge_max_owner_bytes,
        "max_file_bytes": config.knowledge_max_file_bytes
    }


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
def upload_knowledge(body: UploadKnowledgeRequest, request: Request) -> dict[str, Any]:
    owner = caller(request)
    authorize(request, IdentityAccessAction.KNOWLEDGE_UPLOAD, format_knowledge_collection_vrn(owner.entity_id))

    config = request.app.state.config
    store = request.app.state.knowledge_store
    size_bytes = len(body.content.encode("utf-8"))

    if size_bytes > config.knowledge_max_file_bytes:
        raise HTTPException(
            status_code = 413,
            detail = f"'{body.title}' is {size_bytes} bytes; one document may be at most "
                f"{config.knowledge_max_file_bytes} bytes."
        )
    if store.used_bytes(owner.entity_id) + size_bytes > config.knowledge_max_owner_bytes:
        raise HTTPException(
            status_code = 413,
            detail = f"'{body.title}' does not fit in your remaining storage — delete a document "
                f"or upload a smaller one."
        )

    document_id = uuid4().hex
    try:
        entries = request.app.state.rag_indexer.index(document_id, body.title, body.content)
    except Exception as error:
        raise HTTPException(
            status_code = 502,
            detail = f"The document could not be indexed: {type(error).__name__}: {error}"
        ) from None

    if not entries:
        raise HTTPException(status_code = 400, detail = f"'{body.title}' has no text to index.")

    document = KnowledgeDocument(
        id = document_id,
        owner_id = owner.entity_id,
        title = body.title,
        size_bytes = size_bytes,
        chunk_count = len(entries)
    )
    store.add_document(document, entries)
    return {"document": _describe(document), "usage": _usage(request, owner.entity_id)}


@knowledge_router.delete("/{document_id}")
def delete_knowledge(document_id: str, request: Request) -> Response:
    caller(request)
    document = request.app.state.knowledge_store.get_document(document_id)
    if document is None:
        raise HTTPException(status_code = 404, detail = "No such document.")

    authorize(request, IdentityAccessAction.KNOWLEDGE_DELETE, document.vrn)
    request.app.state.knowledge_store.delete_document(document_id)
    return Response(status_code = 204)
