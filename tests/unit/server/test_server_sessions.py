from fastapi.testclient import TestClient

from db import DatabaseSqlite
from app.server.server import app
from app.server.config import Config
from app.intelligence.messages import MessageAI
from app.server.chat_sessions import ChatSession
from app.server.builders import install_security
from app.intelligence.messages import MessageHuman
from app.server.security import IdentityEntityType
from app.server.chat_sessions import ChatSessionStoreSql
from app.server.security import IdentityAccessStoreInMemory
from app.server.security import AuthenticationPasswordHasher

PASSWORD = "a-long-enough-password"


def make_client():
    app.state.config = Config()
    install_security(
        app.state, IdentityAccessStoreInMemory(), AuthenticationPasswordHasher(cost = 16, block_size = 1), "t" * 32
    )
    database = DatabaseSqlite()
    database.start()
    app.state.chat_session_store = ChatSessionStoreSql(database)
    for current_type, current_name in [(IdentityEntityType.ADMIN, "root"), (IdentityEntityType.USER, "ana"), (IdentityEntityType.USER, "bob")]:
        app.state.identity_access_service.create_entity(current_type, current_name, PASSWORD)
    return TestClient(app)


def sign_in(client, name):
    client.post("/api/auth/login", json = {"name": name, "password": PASSWORD})
    return client.get("/api/auth/me").json()["entity_id"]


def store_session(owner_id, title = "A chat"):
    session = ChatSession(
        owner_id = owner_id,
        title = title,
        messages = [MessageHuman(content = "question"), MessageAI(content = "answer")]
    )
    app.state.chat_session_store.create_session(session)
    return session


class TestServerSessions:
    def test_listing_needs_a_session(self):
        assert make_client().get("/api/sessions").status_code == 401

    def test_a_user_lists_only_their_own_conversations(self):
        client = make_client()
        ana = sign_in(client, "ana")
        mine = store_session(ana, "mine")
        store_session(app.state.identity_access_service.find_entity("bob").id, "bob's")
        listed = client.get("/api/sessions").json()
        assert [current["id"] for current in listed] == [mine.id]
        assert listed[0]["title"] == "mine" and listed[0]["message_count"] == 2

    def test_reading_returns_the_turns_with_their_roles(self):
        client = make_client()
        session = store_session(sign_in(client, "ana"))
        body = client.get(f"/api/sessions/{session.id}").json()
        assert body["messages"] == [
            {"role": "human", "agent": None, "sources": [], "content": "question"},
            {"role": "ai", "agent": None, "sources": [], "content": "answer"}
        ]

    def test_an_answer_keeps_the_agent_that_wrote_it_and_its_sources(self):
        client = make_client()
        owner = sign_in(client, "ana")
        sources = [{"index": 1, "title": "guide.md", "excerpt": "Error E1042"}]
        session = ChatSession(owner_id = owner, messages = [
            MessageHuman(content = "q"),
            MessageAI(content = "a [1]", name = "rag", response_metadata = {"sources": sources})
        ])
        app.state.chat_session_store.create_session(session)
        answer = client.get(f"/api/sessions/{session.id}").json()["messages"][1]
        assert answer["agent"] == "rag" and answer["sources"] == sources

    def test_reading_someone_elses_conversation_is_403(self):
        client = make_client()
        sign_in(client, "ana")
        others = store_session(app.state.identity_access_service.find_entity("bob").id)
        assert client.get(f"/api/sessions/{others.id}").status_code == 403

    def test_reading_an_unknown_conversation_is_404(self):
        client = make_client()
        sign_in(client, "ana")
        assert client.get("/api/sessions/missing").status_code == 404

    def test_without_a_session_even_an_unknown_id_is_401_not_404(self):
        assert make_client().get("/api/sessions/missing").status_code == 401

    def test_an_admin_may_read_anyones_conversation(self):
        client = make_client()
        others = store_session(app.state.identity_access_service.find_entity("bob").id)
        sign_in(client, "root")
        assert client.get(f"/api/sessions/{others.id}").status_code == 200

    def test_deleting_removes_the_conversation(self):
        client = make_client()
        session = store_session(sign_in(client, "ana"))
        assert client.delete(f"/api/sessions/{session.id}").status_code == 204
        assert client.get(f"/api/sessions/{session.id}").status_code == 404

    def test_deleting_someone_elses_conversation_is_403_and_leaves_it(self):
        client = make_client()
        sign_in(client, "ana")
        others = store_session(app.state.identity_access_service.find_entity("bob").id)
        assert client.delete(f"/api/sessions/{others.id}").status_code == 403
        assert app.state.chat_session_store.get_session(others.id) is not None

    def test_a_guest_has_conversations_of_its_own(self):
        client = make_client()
        client.post("/api/auth/guest")
        guest = client.get("/api/auth/me").json()["entity_id"]
        session = store_session(guest)
        assert [current["id"] for current in client.get("/api/sessions").json()] == [session.id]

    def test_streaming_into_an_unknown_conversation_is_404(self):
        client = make_client()
        sign_in(client, "ana")
        response = client.get("/api/chat/stream", params = {"message": "hi", "session_id": "missing"})
        assert response.status_code == 404

    def test_streaming_into_someone_elses_conversation_is_403(self):
        client = make_client()
        sign_in(client, "ana")
        others = store_session(app.state.identity_access_service.find_entity("bob").id)
        response = client.get("/api/chat/stream", params = {"message": "hi", "session_id": others.id})
        assert response.status_code == 403
