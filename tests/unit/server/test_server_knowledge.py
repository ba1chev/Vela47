import base64
from fastapi.testclient import TestClient

from db import DatabaseSqlite
from app.server.server import app
from app.server.config import Config
from app.intelligence.web import WebFetcher
from app.intelligence.agents import RagIndexer
from app.intelligence.web import WebAddressGuard
from app.server.builders import install_security
from app.server.knowledge import KnowledgeStoreSql
from app.server.security import IdentityEntityType
from app.intelligence.agents import RagChunkerRecursive
from app.server.chat_sessions import ChatSessionStoreSql
from tests.fixtures.web.fake_resolver import FakeResolver
from tests.fixtures.loaders.pdf_builder import PdfBuilder
from app.server.security import IdentityAccessStoreInMemory
from tests.fixtures.loaders.docx_builder import DocxBuilder
from app.server.security import AuthenticationPasswordHasher
from tests.fixtures.web.fake_web_server import FakeWebServer
from tests.fixtures.model.fake_embeddings import FakeEmbeddings

PASSWORD = "a-long-enough-password"


def make_client(max_file_bytes = 1000, max_owner_bytes = 1500, max_upload_bytes = 100_000, routes = None):
    app.state.config = Config(
        knowledge_max_file_bytes = max_file_bytes,
        knowledge_max_owner_bytes = max_owner_bytes,
        knowledge_max_upload_bytes = max_upload_bytes
    )
    app.state.web_fetcher = WebFetcher(WebAddressGuard(FakeResolver()), transport = FakeWebServer(routes).transport)
    install_security(app.state, IdentityAccessStoreInMemory(), AuthenticationPasswordHasher(cost = 16, block_size = 1), "t" * 32)
    database = DatabaseSqlite()
    database.start()
    app.state.chat_session_store = ChatSessionStoreSql(database)
    app.state.knowledge_store = KnowledgeStoreSql(database)
    app.state.rag_indexer = RagIndexer(RagChunkerRecursive(chunk_chars = 60, overlap_chars = 0), FakeEmbeddings())
    for current_name in ["ana", "bob"]:
        app.state.identity_access_service.create_entity(IdentityEntityType.USER, current_name, PASSWORD)
    return TestClient(app)


def sign_in(client, name):
    client.post("/api/auth/login", json = {"name": name, "password": PASSWORD})


def upload(client, title = "guide.md", content = "Error E1042 means the RDS secret could not be read."):
    return client.post("/api/knowledge", json = {"title": title, "content": content})


def upload_file(client, title, data, content_type = None):
    body = {"title": title, "content_base64": base64.b64encode(data).decode("ascii"), "content_type": content_type}
    return client.post("/api/knowledge", json = body)


def import_url(client, url, title = None):
    return client.post("/api/knowledge/url", json = {"url": url, "title": title})


class TestServerKnowledge:
    def test_everything_needs_a_session(self):
        client = make_client()
        assert client.get("/api/knowledge").status_code == 401
        assert upload(client).status_code == 401
        assert client.delete("/api/knowledge/anything").status_code == 401

    def test_an_upload_is_indexed_and_reported_with_the_new_usage(self):
        client = make_client()
        sign_in(client, "ana")
        response = upload(client)
        assert response.status_code == 201
        body = response.json()
        assert body["document"]["title"] == "guide.md" and body["document"]["chunk_count"] == 1
        assert body["usage"] == {
            "used_bytes": body["document"]["size_bytes"], "max_bytes": 1500, "max_file_bytes": 1000, "max_upload_bytes": 100_000
        }

    def test_the_listing_carries_the_limit_the_sidebar_draws(self):
        client = make_client()
        sign_in(client, "ana")
        upload(client)
        body = client.get("/api/knowledge").json()
        assert len(body["documents"]) == 1 and body["usage"]["used_bytes"] > 0 and body["usage"]["max_bytes"] == 1500

    def test_a_document_larger_than_the_file_limit_is_413(self):
        client = make_client(max_file_bytes = 10)
        sign_in(client, "ana")
        assert upload(client).status_code == 413

    def test_the_limit_counts_utf8_bytes_not_characters(self):
        client = make_client(max_file_bytes = 10)
        sign_in(client, "ana")
        assert upload(client, content = "ж" * 6).status_code == 413

    def test_an_upload_that_would_exceed_the_owners_storage_is_413(self):
        client = make_client(max_file_bytes = 1000, max_owner_bytes = 120)
        sign_in(client, "ana")
        assert upload(client, content = "a " * 40).status_code == 201
        assert upload(client, content = "b " * 40).status_code == 413

    def test_each_owner_sees_only_their_documents(self):
        client = make_client()
        sign_in(client, "ana")
        upload(client)
        sign_in(client, "bob")
        assert client.get("/api/knowledge").json()["documents"] == []

    def test_deleting_frees_the_storage(self):
        client = make_client()
        sign_in(client, "ana")
        document_id = upload(client).json()["document"]["id"]
        assert client.delete(f"/api/knowledge/{document_id}").status_code == 204
        assert client.get("/api/knowledge").json()["usage"]["used_bytes"] == 0
        assert client.delete(f"/api/knowledge/{document_id}").status_code == 404

    def test_deleting_someone_elses_document_is_403(self):
        client = make_client()
        sign_in(client, "ana")
        document_id = upload(client).json()["document"]["id"]
        sign_in(client, "bob")
        assert client.delete(f"/api/knowledge/{document_id}").status_code == 403

    def test_a_guest_keeps_documents_of_its_own(self):
        client = make_client()
        client.post("/api/auth/guest")
        assert upload(client).status_code == 201

    def test_an_unknown_agent_is_rejected_before_anything_runs(self):
        client = make_client()
        sign_in(client, "ana")
        assert client.get("/api/chat/stream", params = {"message": "hi", "agent": "oracle"}).status_code == 422

    def test_the_rag_agent_needs_a_session_like_any_other(self):
        assert make_client().get("/api/chat/stream", params = {"message": "hi", "agent": "rag"}).status_code == 401

    def test_a_pdf_is_uploaded_as_base64_and_its_text_indexed(self):
        client = make_client()
        sign_in(client, "ana")
        response = upload_file(client, "report.pdf", PdfBuilder().build(["Revenue grew in Q3."]), "application/pdf")
        assert response.status_code == 201
        assert response.json()["document"]["size_bytes"] == len("Revenue grew in Q3.")

    def test_a_word_document_is_uploaded_and_its_text_indexed(self):
        client = make_client()
        sign_in(client, "ana")
        response = upload_file(client, "runbook.docx", DocxBuilder().build(), "")
        assert response.status_code == 201 and response.json()["document"]["chunk_count"] >= 1

    def test_an_html_file_counts_its_text_not_its_markup(self):
        client = make_client()
        sign_in(client, "ana")
        markup = "<html><head><style>" + "p{}" * 200 + "</style></head><body><p>Short text.</p></body></html>"
        response = upload(client, title = "page.html", content = markup)
        assert response.status_code == 201 and response.json()["document"]["size_bytes"] == len("Short text.")

    def test_a_format_no_loader_reads_is_415(self):
        client = make_client()
        sign_in(client, "ana")
        assert upload_file(client, "photo.png", b"\x89PNG", "image/png").status_code == 415

    def test_a_file_that_cannot_be_read_is_400_with_the_reason(self):
        client = make_client()
        sign_in(client, "ana")
        response = upload_file(client, "scan.pdf", PdfBuilder().build([""]), "application/pdf")
        assert response.status_code == 400 and "no text layer" in response.json()["detail"]

    def test_a_damaged_pdf_is_400_not_a_server_error(self):
        client = make_client()
        sign_in(client, "ana")
        damaged = PdfBuilder().build(["x"]).replace(b"/Size 6 /Root 1 0 R", b"/Size /Six /Root 9 0 R")
        response = upload_file(client, "broken.pdf", damaged, "application/pdf")
        assert response.status_code == 400 and "not a readable PDF" in response.json()["detail"]

    def test_content_that_is_not_base64_is_400(self):
        client = make_client()
        sign_in(client, "ana")
        response = client.post("/api/knowledge", json = {"title": "a.pdf", "content_base64": "not base64!"})
        assert response.status_code == 400

    def test_both_or_neither_content_is_422(self):
        client = make_client()
        sign_in(client, "ana")
        assert client.post("/api/knowledge", json = {"title": "a.md"}).status_code == 422
        assert client.post("/api/knowledge", json = {"title": "a.md", "content": "x", "content_base64": "eA=="}).status_code == 422

    def test_a_file_over_the_upload_limit_is_413_before_it_is_read(self):
        client = make_client(max_upload_bytes = 100)
        sign_in(client, "ana")
        assert upload_file(client, "big.pdf", b"%PDF" + b"x" * 200, "application/pdf").status_code == 413

    def test_a_page_is_imported_by_url_under_its_own_title(self):
        page = "<html><head><title>Release notes</title></head><body><p>Hybrid search shipped.</p></body></html>"
        client = make_client(routes = {"https://example.org/notes": FakeWebServer.page(page)})
        sign_in(client, "ana")
        response = import_url(client, "https://example.org/notes")
        assert response.status_code == 201 and response.json()["document"]["title"] == "Release notes"

    def test_an_imported_page_can_be_named_by_the_caller(self):
        client = make_client(routes = {"https://example.org/notes": FakeWebServer.page("<p>Text.</p>")})
        sign_in(client, "ana")
        assert import_url(client, "https://example.org/notes", title = "Notes").json()["document"]["title"] == "Notes"

    def test_a_page_without_a_title_is_listed_under_its_url(self):
        client = make_client(routes = {"https://example.org/plain": FakeWebServer.page("Just text.", "text/plain")})
        sign_in(client, "ana")
        assert import_url(client, "https://example.org/plain").json()["document"]["title"] == "https://example.org/plain"

    def test_a_private_address_cannot_be_imported(self):
        client = make_client()
        sign_in(client, "ana")
        response = import_url(client, "http://169.254.169.254/latest/meta-data/iam/security-credentials/")
        assert response.status_code == 400 and "not a public address" in response.json()["detail"]

    def test_a_page_larger_than_the_upload_limit_is_413(self):
        client = make_client(max_upload_bytes = 100, routes = {"https://example.org/big": FakeWebServer.page("x" * 500)})
        sign_in(client, "ana")
        assert import_url(client, "https://example.org/big").status_code == 413

    def test_importing_a_url_needs_a_session(self):
        assert import_url(make_client(), "https://example.org/").status_code == 401
