import base64
import binascii
from uuid import uuid4
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Request, Response

from app.server.routes import caller
from app.server.routes import authorize
from app.intelligence.loaders import LoaderType
from app.intelligence.web import WebAccessError
from app.server.knowledge import KnowledgeDocument
from app.intelligence.loaders import LoadersFactory
from app.intelligence.loaders import LoaderDocument
from app.server.security import IdentityAccessAction
from app.server.requests import UploadKnowledgeRequest
from app.intelligence.loaders import resolve_loader_type
from app.server.requests import ImportKnowledgeUrlRequest
from app.server.security import format_knowledge_collection_vrn

knowledge_router = APIRouter(prefix = "/api/knowledge")

READABLE_FORMATS = "text, Markdown, CSV, JSON, HTML, PDF or Word (.docx)"


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
        "max_file_bytes": config.knowledge_max_file_bytes,
        "max_upload_bytes": config.knowledge_max_upload_bytes
    }


def _read(title: str, loader_type: Optional[LoaderType], data: bytes,
    encoding: Optional[str] = None) -> LoaderDocument:
    """The text inside an uploaded or fetched file, by the loader its type calls for. A
    format no loader reads is 415; a file of a known format that cannot be read — a
    broken PDF, a scan without a text layer — is 400 with the loader's explanation."""
    if loader_type is None:
        raise HTTPException(
            status_code = 415,
            detail = f"'{title}' is not a format that can be read — use {READABLE_FORMATS}."
        )
    try:
        return LoadersFactory().create(loader_type).load(data, encoding)
    except ValueError as error:
        raise HTTPException(status_code = 400, detail = f"'{title}' could not be read: {error}") from None


def _ingest(request: Request, owner_id: str, title: str, text: str) -> dict[str, Any]:
    """Indexes extracted text as one of the owner's documents — the part every way of
    adding a document shares. The limits count the text that is kept, not the file it
    came from, since the text is what is stored, embedded and searched."""
    config = request.app.state.config
    store = request.app.state.knowledge_store
    size_bytes = len(text.encode("utf-8"))

    if not text.strip():
        raise HTTPException(status_code = 400, detail = f"'{title}' has no text to index.")
    if size_bytes > config.knowledge_max_file_bytes:
        raise HTTPException(
            status_code = 413,
            detail = f"'{title}' holds {size_bytes} bytes of text; one document may hold at most "
                f"{config.knowledge_max_file_bytes} bytes."
        )
    if store.used_bytes(owner_id) + size_bytes > config.knowledge_max_owner_bytes:
        raise HTTPException(
            status_code = 413,
            detail = f"'{title}' does not fit in your remaining storage — delete a document "
                f"or upload a smaller one."
        )

    document_id = uuid4().hex
    try:
        entries = request.app.state.rag_indexer.index(document_id, title, text)
    except Exception as error:
        raise HTTPException(
            status_code = 502,
            detail = f"The document could not be indexed: {type(error).__name__}: {error}"
        ) from None

    if not entries:
        raise HTTPException(status_code = 400, detail = f"'{title}' has no text to index.")

    document = KnowledgeDocument(
        id = document_id,
        owner_id = owner_id,
        title = title,
        size_bytes = size_bytes,
        chunk_count = len(entries)
    )
    store.add_document(document, entries)
    return {"document": _describe(document), "usage": _usage(request, owner_id)}


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
    """Text arrives as text and is read as text — or as a page, when its name or type says
    it is HTML. Anything else arrives base64 encoded and is read by whichever loader its
    type and name call for."""
    owner = caller(request)
    authorize(request, IdentityAccessAction.KNOWLEDGE_UPLOAD, format_knowledge_collection_vrn(owner.entity_id))

    config = request.app.state.config
    resolved = resolve_loader_type(body.title, body.content_type)

    if body.content is not None:
        data = body.content.encode("utf-8")
        loader_type = LoaderType.HTML if resolved is LoaderType.HTML else LoaderType.TEXT
    else:
        try:
            data = base64.b64decode(body.content_base64 or "", validate = True)
        except (binascii.Error, ValueError):
            raise HTTPException(status_code = 400, detail = f"'{body.title}' was not sent as valid base64.") from None
        loader_type = resolved

    if len(data) > config.knowledge_max_upload_bytes:
        raise HTTPException(
            status_code = 413,
            detail = f"'{body.title}' is {len(data)} bytes; a file may be at most "
                f"{config.knowledge_max_upload_bytes} bytes."
        )

    document = _read(body.title, loader_type, data)
    return _ingest(request, owner.entity_id, body.title, document.text)


@knowledge_router.post("/url", status_code = 201)
def import_knowledge_url(body: ImportKnowledgeUrlRequest, request: Request) -> dict[str, Any]:
    """Adds a web page, or a PDF or Word document online, by its URL. It is fetched by the
    same WebFetcher the agents use — public addresses only, size and time bounded — and
    listed under the title it gives itself unless the caller names one."""
    owner = caller(request)
    authorize(request, IdentityAccessAction.KNOWLEDGE_UPLOAD, format_knowledge_collection_vrn(owner.entity_id))

    config = request.app.state.config
    try:
        page = request.app.state.web_fetcher.fetch(body.url, max_bytes = config.knowledge_max_upload_bytes)
    except WebAccessError as error:
        raise HTTPException(status_code = 400, detail = f"The page could not be fetched: {error}") from None

    if page.truncated:
        raise HTTPException(
            status_code = 413,
            detail = f"{page.url} is larger than the {config.knowledge_max_upload_bytes} bytes a file may be."
        )

    document = _read(page.url, resolve_loader_type(page.url, page.content_type), page.content, page.encoding)
    title = (body.title or document.title or page.url).strip()[:200]
    return _ingest(request, owner.entity_id, title, document.text)


@knowledge_router.delete("/{document_id}")
def delete_knowledge(document_id: str, request: Request) -> Response:
    caller(request)
    document = request.app.state.knowledge_store.get_document(document_id)
    if document is None:
        raise HTTPException(status_code = 404, detail = "No such document.")

    authorize(request, IdentityAccessAction.KNOWLEDGE_DELETE, document.vrn)
    request.app.state.knowledge_store.delete_document(document_id)
    return Response(status_code = 204)
