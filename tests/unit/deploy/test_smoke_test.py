from fastapi.testclient import TestClient

from app.server.server import app
from app.server.config import Config
from deploy.pipeline import SmokeTest
from app.server.builders import install_security
from app.server.security import IdentityAccessStoreInMemory
from app.server.config_environment import ConfigEnvironment
from app.server.security import AuthenticationPasswordHasher


class SessionStoreWithNothing:
    def list_sessions(self, owner_id):
        return []


def serve(version):
    app.state.config = Config.model_construct(environment = ConfigEnvironment.DEV, version = version)
    install_security(app.state, IdentityAccessStoreInMemory(), AuthenticationPasswordHasher(cost = 16, block_size = 1), "t" * 32)
    app.state.chat_session_store = SessionStoreWithNothing()
    client = TestClient(app, base_url = "https://vela47-dev.y47.sevc.link")

    def fetch(method, url, headers):
        response = client.request(method, url, headers = headers)
        return response.status_code, dict(response.headers), response.content
    return fetch


def unreachable(method, url, headers):
    raise ConnectionError("connection refused")


class TestSmokeTest:
    def test_a_server_running_the_release_passes(self):
        assert SmokeTest("https://vela47-dev.y47.sevc.link", "1.4.0", serve("1.4.0"), attempts = 1).run() == []

    def test_a_server_still_running_the_old_release_fails(self):
        problems = SmokeTest("https://vela47-dev.y47.sevc.link", "1.4.0", serve("1.3.0"), attempts = 2, wait_seconds = 0).run()
        assert problems == ["the health endpoint reports version 1.3.0, not 1.4.0"]

    def test_an_unreachable_server_fails(self):
        problems = SmokeTest("https://vela47-dev.y47.sevc.link", "1.4.0", unreachable, attempts = 2, wait_seconds = 0).run()
        assert problems[0].startswith("the health endpoint is unreachable")
