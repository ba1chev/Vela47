import base64
import binascii
from uuid import uuid4
from typing import Any, Optional
from contextlib import AbstractContextManager

from app.server.config import Config
from app.intelligence.web import WebFetcher
from app.intelligence.agents import RagIndexer
from app.intelligence.loaders import LoaderType
from app.intelligence.web import WebAccessError
from app.server.knowledge import KnowledgeDocument
from app.intelligence.loaders import LoadersFactory
from app.intelligence.loaders import LoaderDocument
from app.intelligence.tracing import TraceEventType
from app.server.knowledge import KnowledgeStoreBase
from app.intelligence.security import SecurityMonitor
from app.server.requests import UploadKnowledgeRequest
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.loaders import resolve_loader_type
from app.intelligence.security import SecurityPromptType
from app.server.knowledge import KnowledgeIngestionError
from app.server.requests import ImportKnowledgeUrlRequest

READABLE_FORMATS = "text, Markdown, CSV, JSON, HTML, PDF or Word (.docx)"
EXCERPT_CHARS = 1000


class KnowledgeIngestion:
    """Adds one document to an owner's knowledge, from an upload or from a URL: receive
    or fetch it, extract its text, check it against the limits, have RagIndexer chunk,
    embed and describe it, and store it. One instance per request, holding the tracer of
    that request, so every stage, down to the chunker's A* search and each address the
    fetcher checked, is a span of one trace the browser watches live.

    The chunks are also inspected for poisoning, in monitor mode like every other check:
    the trace shows what a later question would retrieve, and nothing is refused for it.
    A failure raises KnowledgeIngestionError with the status the route answers with."""

    def __init__(self, config: Config, knowledge_store: KnowledgeStoreBase, rag_indexer: RagIndexer,
        web_fetcher: WebFetcher, tracing_service: TracingServiceBase) -> None:
        self._config: Config = config
        self._knowledge_store: KnowledgeStoreBase = knowledge_store
        self._rag_indexer: RagIndexer = rag_indexer
        self._web_fetcher: WebFetcher = web_fetcher
        self._tracing_service: TracingServiceBase = tracing_service

    def _layer(self, label: str, payload: Optional[dict[str, Any]] = None) -> AbstractContextManager[dict[str, Any]]:
        return self._tracing_service.span(TraceEventType.LAYER_STARTED, TraceEventType.LAYER_FINISHED, label, payload)

    def _pipeline(self, label: str, payload: dict[str, Any]) -> AbstractContextManager[dict[str, Any]]:
        return self._tracing_service.span(
            TraceEventType.PIPELINE_STARTED, TraceEventType.PIPELINE_FINISHED, label, {"agent": "ingest", **payload}
        )

    def upload(self, owner_id: str, body: UploadKnowledgeRequest) -> KnowledgeDocument:
        with self._pipeline(f"Upload · {body.title}", {"title": body.title}) as span:
            with self._layer("Receive") as receive:
                data, loader_type = self._receive(body)
                receive["detail"] = f"{len(data)} bytes, read as {loader_type.value if loader_type else 'an unknown format'}"
            document = self._extract(body.title, loader_type, data)
            stored = self._ingest(owner_id, body.title, document.text)
            span.update({"document_id": stored.id, "chunks": stored.chunk_count, "detail": f"{stored.chunk_count} chunks stored"})
        return stored

    def import_url(self, owner_id: str, body: ImportKnowledgeUrlRequest) -> KnowledgeDocument:
        with self._pipeline(f"Import · {body.url}", {"url": body.url}) as span:
            with self._layer("Fetch", {"url": body.url}) as fetch:
                try:
                    page = self._web_fetcher.fetch(body.url, max_bytes = self._config.knowledge_max_upload_bytes)
                except WebAccessError as error:
                    raise KnowledgeIngestionError(400, f"The page could not be fetched: {error}") from None
                if page.truncated:
                    raise KnowledgeIngestionError(
                        413, f"{page.url} is larger than the {self._config.knowledge_max_upload_bytes} bytes a file may be."
                    )
                fetch["detail"] = f"{len(page.content)} bytes of {page.content_type or 'unknown type'} from {page.url}"

            document = self._extract(page.url, resolve_loader_type(page.url, page.content_type), page.content, page.encoding)
            title = ((body.title or "").strip() or (document.title or "").strip() or page.url)[:200]
            self._tracing_service.record("Title", "loader", {
                "detail": f"listed as “{title}”",
                "given": body.title,
                "declared": document.title,
                "url": page.url,
                "chosen": title
            })
            stored = self._ingest(owner_id, title, document.text)
            span.update({"document_id": stored.id, "chunks": stored.chunk_count, "detail": f"{stored.chunk_count} chunks stored"})
        return stored

    def _receive(self, body: UploadKnowledgeRequest) -> tuple[bytes, Optional[LoaderType]]:
        resolved = resolve_loader_type(body.title, body.content_type)
        if body.content is not None:
            data = body.content.encode("utf-8")
            loader_type = LoaderType.HTML if resolved is LoaderType.HTML else LoaderType.TEXT
            transport = {"transport": "text", "characters": len(body.content)}
        else:
            try:
                data = base64.b64decode(body.content_base64 or "", validate = True)
            except (binascii.Error, ValueError):
                raise KnowledgeIngestionError(400, f"'{body.title}' was not sent as valid base64.") from None
            loader_type = resolved
            transport = {"transport": "base64", "encoded_characters": len(body.content_base64 or "")}

        self._tracing_service.record("Request", "http", {
            "detail": f"{body.title}, {len(data)} bytes as {transport['transport']}",
            "title": body.title,
            "content_type": body.content_type,
            "bytes": len(data),
            **transport
        })
        self._tracing_service.record("Format", "loader", {
            "detail": f"{loader_type.value if loader_type else 'unreadable'} from "
                f"{'the media type ' + body.content_type if body.content_type else 'the file name'}",
            "content_type": body.content_type,
            "resolved": resolved.value if resolved else None,
            "loader": loader_type.value if loader_type else None
        })
        limit = self._config.knowledge_max_upload_bytes
        self._tracing_service.record("Upload limit", "quota", {
            "detail": f"{len(data)} of at most {limit} bytes",
            "bytes": len(data),
            "max_upload_bytes": limit,
            "ok": len(data) <= limit
        })
        if len(data) > limit:
            raise KnowledgeIngestionError(413, f"'{body.title}' is {len(data)} bytes; a file may be at most {limit} bytes.")
        return data, loader_type

    def _extract(self, title: str, loader_type: Optional[LoaderType], data: bytes,
        encoding: Optional[str] = None) -> LoaderDocument:
        with self._layer("Extraction", {"loader": loader_type.value if loader_type else None}) as span:
            if loader_type is None:
                raise KnowledgeIngestionError(415, f"'{title}' is not a format that can be read — use {READABLE_FORMATS}.")
            loader = LoadersFactory().create(loader_type)
            try:
                document = loader.load(data, encoding)
            except ValueError as error:
                raise KnowledgeIngestionError(400, f"'{title}' could not be read: {error}") from None

            text = document.text
            span.update({
                "loader_class": type(loader).__name__,
                "declared_title": document.title,
                "characters": len(text),
                "words": len(text.split()),
                "lines": text.count("\n") + 1 if text else 0,
                "paragraphs": len([current for current in text.split("\n\n") if current.strip()]),
                "excerpt": text[:EXCERPT_CHARS],
                **document.details,
                "detail": f"{len(text)} characters, {len(text.split())} words by {type(loader).__name__}"
            })
        return document

    def _ingest(self, owner_id: str, title: str, text: str) -> KnowledgeDocument:
        size_bytes = len(text.encode("utf-8"))
        with self._layer("Validation") as span:
            used = self._knowledge_store.used_bytes(owner_id)
            self._tracing_service.record("Text", "quota", {
                "detail": f"{size_bytes} bytes of text, at most {self._config.knowledge_max_file_bytes} per document",
                "bytes": size_bytes,
                "max_file_bytes": self._config.knowledge_max_file_bytes,
                "empty": not text.strip()
            })
            self._tracing_service.record("Storage left", "quota", {
                "detail": f"{used} of {self._config.knowledge_max_owner_bytes} bytes used, this adds {size_bytes}",
                "used_bytes": used,
                "adding_bytes": size_bytes,
                "max_bytes": self._config.knowledge_max_owner_bytes,
                "remaining_bytes": self._config.knowledge_max_owner_bytes - used
            })
            if not text.strip():
                raise KnowledgeIngestionError(400, f"'{title}' has no text to index.")
            if size_bytes > self._config.knowledge_max_file_bytes:
                raise KnowledgeIngestionError(
                    413,
                    f"'{title}' holds {size_bytes} bytes of text; one document may hold at most "
                    f"{self._config.knowledge_max_file_bytes} bytes."
                )
            if used + size_bytes > self._config.knowledge_max_owner_bytes:
                raise KnowledgeIngestionError(
                    413,
                    f"'{title}' does not fit in your remaining storage — delete a document or upload a smaller one."
                )
            span["detail"] = "within every limit"

        document_id = uuid4().hex
        try:
            entries = self._rag_indexer.index(document_id, title, text)
        except Exception as error:
            raise KnowledgeIngestionError(
                502, f"The document could not be indexed: {type(error).__name__}: {error}"
            ) from None
        if not entries:
            raise KnowledgeIngestionError(400, f"'{title}' has no text to index.")

        with self._layer("Security", {"chunks": len(entries)}) as span:
            monitor = SecurityMonitor(self._tracing_service)
            verdicts = [
                monitor.inspect(SecurityPromptType.POISONING, current_entry.message.content, f"{title}, part {index + 1}")
                for index, current_entry in enumerate(entries)
            ]
            flagged = sum(current_verdict.flagged for current_verdict in verdicts)
            span.update({"flagged": flagged, "detail": f"{len(verdicts)} chunks checked for poisoning, {flagged} flagged"})

        document = KnowledgeDocument(
            id = document_id, owner_id = owner_id, title = title, size_bytes = size_bytes, chunk_count = len(entries)
        )
        with self._layer("Storage", {"document_id": document_id}) as span:
            self._knowledge_store.add_document(document, entries)
            span.update({
                "rows": len(entries) + 1,
                "used_bytes": self._knowledge_store.used_bytes(owner_id),
                "detail": f"1 document and {len(entries)} chunks written"
            })
        return document
