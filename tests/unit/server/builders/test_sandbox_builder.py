import re
import pathlib

from app.server.builders import build_sandbox_pool
from app.server.builders import SANDBOX_COMPOSE_FILE
from app.server.builders import SANDBOX_FUNCTION_NAME
from app.intelligence.sandbox import SandboxPoolLambda
from app.server.config_environment import ConfigEnvironment

PROD = pathlib.Path(__file__).resolve().parents[4] / "deploy" / "prod"


class ProdConfig:
    environment = ConfigEnvironment.PROD
    aws_region = "eu-central-1"


class TestSandboxBuilder:
    def test_development_has_its_compose_project(self):
        assert SANDBOX_COMPOSE_FILE.is_file() and "dev" in SANDBOX_COMPOSE_FILE.parts

    def test_the_development_image_has_pytest_for_the_test_subagent(self):
        assert "pytest" in (SANDBOX_COMPOSE_FILE.parent / "Dockerfile").read_text()

    def test_the_development_network_reaches_nothing(self):
        compose = SANDBOX_COMPOSE_FILE.read_text()
        assert "internal: true" in compose
        assert "gateway_mode_ipv4: isolated" in compose
        assert 'enable_icc: "false"' in compose

    def test_every_development_slot_has_a_name_and_an_address_of_its_own(self):
        compose = SANDBOX_COMPOSE_FILE.read_text()
        names = re.findall(r"container_name: (\S+)", compose)
        addresses = re.findall(r"ipv4_address: (\S+)", compose)
        assert len(names) == len(set(names)) == len(addresses) == len(set(addresses)) == 10

    def test_production_runs_commands_in_the_lambda_function(self):
        pool = build_sandbox_pool(ProdConfig(), 10)
        assert isinstance(pool, SandboxPoolLambda) and len(pool) == 10
        assert pool.acquire().reference == SANDBOX_FUNCTION_NAME

    def test_the_function_the_server_calls_is_the_one_terraform_creates(self):
        variables = (PROD / "variables.tf").read_text()
        default = re.search(r'variable "sandbox_function_name" \{.*?default\s*=\s*"([^"]+)"', variables, re.DOTALL)
        assert default.group(1) == SANDBOX_FUNCTION_NAME

    def test_the_production_image_has_pytest_for_the_test_subagent(self):
        assert "pytest" in (PROD / "images" / "sandbox_lambda" / "Dockerfile").read_text()
