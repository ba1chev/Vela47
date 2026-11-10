import logging
import subprocess

from app.intelligence.sandbox import SandboxPoolBase
from app.intelligence.sandbox import SandboxPoolDocker
from app.intelligence.sandbox import SandboxPoolInMemory

logger = logging.getLogger("vela47")


def _docker_is_available() -> bool:
    try:
        return subprocess.run(
            ["docker", "info"], capture_output = True, timeout = 10, check = False
        ).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def build_sandbox_pool(size: int) -> SandboxPoolBase:
    if _docker_is_available():
        return SandboxPoolDocker()

    logger.warning(
        "Docker is not reachable — falling back to a local sandbox. Subagents can "
        "write files but cannot run commands."
    )
    return SandboxPoolInMemory(size = size)
