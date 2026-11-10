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
    """Containers when Docker is reachable, a bare directory when it is not.

    The fallback is loud rather than silent: without containers the local pool
    refuses to run commands at all, so a TEST subagent fails with an explanation
    instead of quietly executing model-written code on the host.

    size is the fallback's alone. The Docker pool has as many slots as its compose file
    has services."""
    if _docker_is_available():
        return SandboxPoolDocker()

    logger.warning(
        "Docker is not reachable — falling back to a local sandbox. Subagents can "
        "write files but cannot run commands."
    )
    return SandboxPoolInMemory(size = size)
