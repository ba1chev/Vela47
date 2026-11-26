import logging
from fastapi.testclient import TestClient

from app.server.server import app
from app.server.config import Config
from app.server.server_logging import LOGGER_NAME
from app.server.server_logging import configure_logging
from app.server.config_environment import ConfigEnvironment


def make_client(config):
    app.state.config = config
    return TestClient(app)


class TestServerHealth:
    def test_health_answers_without_a_session(self):
        response = make_client(Config()).get("/api/health")
        assert response.status_code == 200 and response.json()["status"] == "ok"

    def test_health_names_the_environment_and_the_release(self):
        config = Config.model_construct(environment = ConfigEnvironment.STAGING, version = "1.4.0")
        body = make_client(config).get("/api/health").json()
        assert body["environment"] == "staging" and body["version"] == "1.4.0"

    def test_a_server_run_from_a_working_tree_has_no_version(self):
        assert make_client(Config()).get("/api/health").json()["version"] is None


class TestServerLogging:
    def test_the_server_logs_at_info_through_one_handler_of_its_own(self):
        logger = configure_logging()
        configure_logging()
        assert logger.name == LOGGER_NAME and logger.level == logging.INFO
        assert [current.get_name() for current in logger.handlers].count(LOGGER_NAME) == 1
        assert logger.propagate is False
