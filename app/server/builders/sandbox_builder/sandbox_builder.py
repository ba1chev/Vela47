import logging
import pathlib
import subprocess

from app.server.config import Config
from app.intelligence.sandbox import SandboxPoolBase
from app.intelligence.sandbox import SandboxPoolDocker
from app.intelligence.sandbox import SandboxPoolInMemory
from app.server.config_environment import ConfigEnvironment

DEPLOY_DIRECTORY = pathlib.Path(__file__).resolve().parents[4] / "deploy"
SANDBOX_COMPOSE_FILES = {
    ConfigEnvironment.DEV: DEPLOY_DIRECTORY / "dev" / "images" / "sandbox_image" / "docker-compose.yaml",
    ConfigEnvironment.PROD: DEPLOY_DIRECTORY / "prod" / "images" / "sandbox_image" / "docker-compose.yaml"
}

logger = logging.getLogger("vela47")


def _docker_is_available() -> bool:
    try:
        return subprocess.run(
            ["docker", "info"], capture_output = True, timeout = 10, check = False
        ).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def build_sandbox_pool(config: Config, size: int) -> SandboxPoolBase:
    if _docker_is_available():
        return SandboxPoolDocker(SANDBOX_COMPOSE_FILES[config.environment])

    logger.warning(
        "Docker is not reachable — falling back to a local sandbox. Subagents can "
        "write files but cannot run commands."
    )
    return SandboxPoolInMemory(size = size)
