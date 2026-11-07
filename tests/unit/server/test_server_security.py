from fastapi.testclient import TestClient

from app.server.server import app
from app.server.config import Config
from app.server.security import IdentityEntityType
from app.server.security_builder import install_security
from app.server.config_environment import ConfigEnvironment
from app.server.security import IdentityAccessStoreInMemory
from app.server.security import AuthenticationPasswordHasher

ADMIN_PASSWORD = "admin-password-long"
USER_PASSWORD = "user-password-long"


def make_client(config = None):
    app.state.config = config or Config()
    install_security(
        app.state, IdentityAccessStoreInMemory(), AuthenticationPasswordHasher(cost = 16, block_size = 1), "t" * 32
    )
    app.state.identity_access_service.create_entity(IdentityEntityType.ADMIN, "root", ADMIN_PASSWORD)
    app.state.identity_access_service.create_entity(IdentityEntityType.USER, "ana", USER_PASSWORD)
    return TestClient(app)


def make_client_keeping_state():
    return TestClient(app)


def sign_in(client, name, password, role = None):
    body = {"name": name, "password": password}
    if role is not None:
        body["role"] = role
    return client.post("/api/auth/login", json = body)


def create_user(client, name = "bob", password = "bob-password-long", type = "user"):
    return client.post("/api/iam/entities", json = {"type": type, "name": name, "password": password})


class TestServerSecurity:
    def test_the_stream_refuses_a_caller_without_a_session(self):
        assert make_client().get("/api/chat/stream", params = {"message": "hi"}).status_code == 401

    def test_the_stream_refuses_a_forged_session(self):
        client = make_client()
        client.cookies.set("vela47_session", "forged.token.value")
        assert client.get("/api/chat/stream", params = {"message": "hi"}).status_code == 401

    def test_a_guest_session_arrives_as_an_http_only_strict_cookie(self):
        response = make_client().post("/api/auth/guest")
        cookie = response.headers["set-cookie"].lower()
        assert response.status_code == 200
        assert "vela47_session=" in cookie
        assert "httponly" in cookie
        assert "samesite=strict" in cookie

    def test_the_cookie_is_not_marked_secure_over_plain_http(self):
        assert "secure" not in make_client().post("/api/auth/guest").headers["set-cookie"].lower()

    def test_the_cookie_is_always_secure_in_prod_because_tls_ends_at_the_load_balancer(self):
        config = Config.model_construct(environment = ConfigEnvironment.PROD)
        assert "secure" in make_client(config).post("/api/auth/guest").headers["set-cookie"].lower()

    def test_the_token_is_never_in_the_response_body(self):
        response = make_client().post("/api/auth/guest")
        token = response.cookies["vela47_session"]
        assert token not in response.text

    def test_me_describes_the_guest(self):
        client = make_client()
        client.post("/api/auth/guest")
        body = client.get("/api/auth/me").json()
        assert body["entity_type"] == "guest" and body["role"] == "guest"

    def test_me_without_a_session_is_401(self):
        assert make_client().get("/api/auth/me").status_code == 401

    def test_a_wrong_password_is_401(self):
        assert sign_in(make_client(), "ana", "wrong-password-long").status_code == 401

    def test_a_user_signs_in_as_the_user_role(self):
        client = make_client()
        assert sign_in(client, "ana", USER_PASSWORD).json()["role"] == "user"
        assert client.get("/api/auth/me").json()["name"] == "ana"

    def test_an_admin_creates_a_user_who_can_then_sign_in(self):
        client = make_client()
        sign_in(client, "root", ADMIN_PASSWORD)
        created = create_user(client)
        assert created.status_code == 201 and created.json()["name"] == "bob"
        assert sign_in(make_client_keeping_state(), "bob", "bob-password-long").status_code == 200

    def test_a_user_cannot_create_entities(self):
        client = make_client()
        sign_in(client, "ana", USER_PASSWORD)
        assert create_user(client).status_code == 403

    def test_a_guest_cannot_create_entities(self):
        client = make_client()
        client.post("/api/auth/guest")
        assert create_user(client).status_code == 403

    def test_nobody_creates_entities_without_a_session(self):
        assert create_user(make_client()).status_code == 401

    def test_an_admin_working_as_the_user_role_cannot_create_entities(self):
        client = make_client()
        assert sign_in(client, "root", ADMIN_PASSWORD, role = "user").json()["role"] == "user"
        assert create_user(client).status_code == 403

    def test_a_user_cannot_sign_in_as_admin(self):
        assert sign_in(make_client(), "ana", USER_PASSWORD, role = "admin").status_code == 403

    def test_logout_ends_the_session(self):
        client = make_client()
        sign_in(client, "ana", USER_PASSWORD)
        assert client.post("/api/auth/logout").status_code == 204
        assert client.get("/api/auth/me").status_code == 401

    def test_an_invalid_name_is_a_400_with_a_readable_reason(self):
        client = make_client()
        sign_in(client, "root", ADMIN_PASSWORD)
        response = create_user(client, name = "no spaces allowed")
        assert response.status_code == 400 and "name" in response.json()["detail"].lower()

    def test_a_taken_name_is_a_400(self):
        client = make_client()
        sign_in(client, "root", ADMIN_PASSWORD)
        assert create_user(client, name = "ana").status_code == 400

    def test_a_guest_account_cannot_be_created(self):
        client = make_client()
        sign_in(client, "root", ADMIN_PASSWORD)
        assert create_user(client, type = "guest").status_code == 400

