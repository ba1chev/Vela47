import logging
import pathlib
import subprocess

from app.server.config import Config
from app.intelligence.sandbox import SandboxPoolBase
from app.server.config_platform import ConfigPlatform
from app.intelligence.sandbox import SandboxPoolDocker
from app.intelligence.sandbox import SandboxPoolLambda
from app.intelligence.sandbox import SandboxPoolInMemory
from app.server.config_environment import ConfigEnvironment

SANDBOX_COMPOSE_FILE = (
    pathlib.Path(__file__).resolve().parents[4] / "deploy" / "images" / "local" / "sandbox" / "docker-compose.yaml"
)
SANDBOX_FUNCTION_NAME_TEMPLATE = "vela47-{environment}-sandbox"

logger = logging.getLogger("vela47")


def _docker_is_available() -> bool:
    try:
        return subprocess.run(
            ["docker", "info"], capture_output = True, timeout = 10, check = False
        ).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def sandbox_function_name(environment: ConfigEnvironment) -> str:
    return SANDBOX_FUNCTION_NAME_TEMPLATE.format(environment = environment.value)


def build_sandbox_pool(config: Config, size: int) -> SandboxPoolBase:
    if config.platform is ConfigPlatform.AWS:
        return SandboxPoolLambda(sandbox_function_name(config.environment), config.aws_region, size)

    if _docker_is_available():
        return SandboxPoolDocker(SANDBOX_COMPOSE_FILE)

    logger.warning(
        "Docker is not reachable — falling back to a local sandbox. Subagents can "
        "write files but cannot run commands."
    )
    return SandboxPoolInMemory(size = size)
