import re
import pathlib

from app.server.builders import build_sandbox_pool
from app.server.builders import SANDBOX_COMPOSE_FILE
from app.server.builders import sandbox_function_name
from app.intelligence.sandbox import SandboxPoolLambda
from app.server.config_environment import ConfigEnvironment

DEPLOY = pathlib.Path(__file__).resolve().parents[4] / "deploy"
ENVIRONMENTS = DEPLOY / "terraform" / "environments"
AWS_SANDBOX_IMAGE = DEPLOY / "images" / "aws" / "sandbox"
AWS_ENVIRONMENTS = [ConfigEnvironment.DEV, ConfigEnvironment.STAGING, ConfigEnvironment.PROD]


class AwsConfig:
    aws_region = "eu-central-1"

    def __init__(self, environment):
        self.environment = environment
        self.platform = environment.platform


class TestSandboxBuilder:
    def test_local_has_its_compose_project(self):
        assert SANDBOX_COMPOSE_FILE.is_file() and "local" in SANDBOX_COMPOSE_FILE.parts

    def test_the_local_image_has_pytest_for_the_test_subagent(self):
        assert "pytest" in (SANDBOX_COMPOSE_FILE.parent / "Dockerfile").read_text()

    def test_the_local_network_reaches_nothing(self):
        compose = SANDBOX_COMPOSE_FILE.read_text()
        assert "internal: true" in compose
        assert "gateway_mode_ipv4: isolated" in compose
        assert 'enable_icc: "false"' in compose

    def test_every_local_slot_has_a_name_and_an_address_of_its_own(self):
        compose = SANDBOX_COMPOSE_FILE.read_text()
        names = re.findall(r"container_name: (\S+)", compose)
        addresses = re.findall(r"ipv4_address: (\S+)", compose)
        assert len(names) == len(set(names)) == len(addresses) == len(set(addresses)) == 10

    def test_every_aws_environment_runs_commands_in_a_lambda_function_of_its_own(self):
        names = set()
        for current_environment in AWS_ENVIRONMENTS:
            pool = build_sandbox_pool(AwsConfig(current_environment), 10)
            assert isinstance(pool, SandboxPoolLambda) and len(pool) == 10
            names.add(pool.acquire().reference)
        assert names == {"vela47-dev-sandbox", "vela47-staging-sandbox", "vela47-prod-sandbox"}

    def test_the_function_the_server_calls_is_the_one_terraform_creates(self):
        for current_environment in AWS_ENVIRONMENTS:
            variables = (ENVIRONMENTS / current_environment.value / "app" / "variables.tf").read_text()
            default = re.search(r'variable "name" \{.*?default\s*=\s*"([^"]+)"', variables, re.DOTALL)
            assert f"{default.group(1)}-sandbox" == sandbox_function_name(current_environment)

    def test_the_aws_image_has_pytest_for_the_test_subagent(self):
        assert "pytest" in (AWS_SANDBOX_IMAGE / "Dockerfile").read_text()
