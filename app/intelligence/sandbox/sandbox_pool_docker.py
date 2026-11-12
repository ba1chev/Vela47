import json
import pathlib
import tempfile
import threading
import subprocess

from app.intelligence.sandbox import SandboxEnv
from app.intelligence.sandbox import SandboxSlot
from app.intelligence.sandbox import SandboxDocker
from app.intelligence.sandbox import SandboxPoolBase

CONTAINER_WORKSPACE_PATH = "/workspace"
SANDBOX_IMAGE_DIRECTORY = (
    pathlib.Path(__file__).resolve().parents[3] / "deploy" / "dev" / "images" / "sandbox_image"
)
SANDBOX_COMPOSE_FILE = SANDBOX_IMAGE_DIRECTORY / "docker-compose.yaml"


class SandboxPoolDocker(SandboxPoolBase):
    """A fixed set of containers started once and reused: the services of the Docker
    Compose project in deploy/dev/images/sandbox_image/, one slot each, read from the
    file through `docker compose config`.

    start() rebuilds the image from cache and recreates every container, so nothing a
    previous process left inside one survives; shutdown() brings the project down. The
    network gives each container a fixed address and nothing to reach with it.

    No host directory is mounted: each command gets a copy of one run's directory (see
    SandboxDocker). Leasing is guarded by a lock, because two requests taking the same
    slot would put two runs in one container at once."""

    def __init__(self, compose_file: pathlib.Path = SANDBOX_COMPOSE_FILE,
        base_directory: pathlib.Path | None = None) -> None:
        self._compose_file: pathlib.Path = pathlib.Path(compose_file)
        self._base_directory: pathlib.Path = (
            pathlib.Path(base_directory)
            if base_directory is not None
            else pathlib.Path(tempfile.mkdtemp(prefix = "vela47-"))
        )
        self._slots: list[SandboxSlot] = []
        self._busy: set[int] = set()
        self._lock: threading.Lock = threading.Lock()

    @property
    def base_directory(self) -> pathlib.Path:
        return self._base_directory

    def _compose(self, *arguments: str, timeout: int = 120) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["docker", "compose", "--file", str(self._compose_file), *arguments],
            capture_output = True,
            text = True,
            timeout = timeout,
            check = False
        )

    def _slots_from(self, configuration: dict) -> list[SandboxSlot]:
        services = configuration.get("services") or {}
        if not services:
            raise RuntimeError(f"The sandbox compose file {self._compose_file} defines no service.")

        unnamed = sorted(current for current in services if not services[current].get("container_name"))
        if unnamed:
            raise RuntimeError(
                f"Every sandbox service needs a container_name to be entered by; "
                f"{', '.join(unnamed)} has none."
            )

        return [
            SandboxSlot(id = index, reference = services[current]["container_name"])
            for index, current in enumerate(sorted(services))
        ]

    def start(self) -> None:
        self._base_directory.mkdir(parents = True, exist_ok = True)

        configured = self._compose("config", "--format", "json", timeout = 30)
        if configured.returncode != 0:
            raise RuntimeError(
                f"Could not read the sandbox compose file {self._compose_file}: {configured.stderr.strip()}"
            )
        slots = self._slots_from(json.loads(configured.stdout))

        started = self._compose(
            "up", "--detach", "--build", "--force-recreate", "--remove-orphans", "--wait",
            timeout = 900
        )
        if started.returncode != 0:
            self.shutdown()
            raise RuntimeError(
                f"Could not start the sandbox containers from {self._compose_file}: "
                f"{started.stderr.strip()[-2000:]}"
            )

        self._slots = slots
        self._busy = set()

    def shutdown(self) -> None:
        self._slots = []
        self._busy = set()
        try:
            self._compose("down", "--timeout", "0", "--remove-orphans")
        except (OSError, subprocess.TimeoutExpired):
            return

    def acquire(self) -> SandboxSlot:
        with self._lock:
            if not self._slots:
                raise RuntimeError(
                    "The Docker sandbox pool has no containers — start() was not called "
                    "or failed."
                )

            for current_slot in self._slots:
                if current_slot.id not in self._busy:
                    self._busy.add(current_slot.id)
                    return current_slot

            raise RuntimeError(
                f"No sandbox slot available — all {len(self._slots)} containers are in use. "
                f"Add a service to the sandbox compose file or reduce how many subagents run at once."
            )

    def release(self, slot: SandboxSlot) -> None:
        with self._lock:
            self._busy.discard(slot.id)

    def env_for(self, slot: SandboxSlot, run_id: str) -> SandboxEnv:
        return SandboxDocker(
            container_name = slot.reference,
            host_directory = self._base_directory / run_id,
            container_directory = CONTAINER_WORKSPACE_PATH
        )

    @property
    def available(self) -> int:
        return len(self._slots) - len(self._busy)

    def __len__(self) -> int:
        return len(self._slots)
