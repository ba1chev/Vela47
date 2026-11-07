from fastapi.testclient import TestClient

from db import DatabaseSqlite
from app.server.server import app
from app.server.config import Config
from app.intelligence.agents import RagIndexer
from app.server.builders import install_security
from app.server.knowledge import KnowledgeStoreSql
from app.server.security import IdentityEntityType
from app.intelligence.agents import RagChunkerRecursive
from app.server.chat_sessions import ChatSessionStoreSql
from app.server.security import IdentityAccessStoreInMemory
from app.server.security import AuthenticationPasswordHasher
from tests.fixtures.model.fake_embeddings import FakeEmbeddings

PASSWORD = "a-long-enough-password"


def make_client(max_file_bytes = 1000, max_owner_bytes = 1500):
    app.state.config = Config(knowledge_max_file_bytes = max_file_bytes, knowledge_max_owner_bytes = max_owner_bytes)
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
        assert body["usage"] == {"used_bytes": body["document"]["size_bytes"], "max_bytes": 1500, "max_file_bytes": 1000}

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
