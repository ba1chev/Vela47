import hashlib
import pathlib
import tempfile
import threading
import subprocess
from typing import Optional

from app.intelligence.sandbox import SandboxEnv
from app.intelligence.sandbox import SandboxSlot
from app.intelligence.sandbox import SandboxDocker
from app.intelligence.sandbox import SandboxPoolBase

CONTAINER_WORKSPACE_PATH = "/workspace"
SANDBOX_IMAGE_DIRECTORY = pathlib.Path(__file__).resolve().parent / "sandbox_image"


class SandboxPoolDocker(SandboxPoolBase):
    """A fixed set of containers started once and reused, like a vending machine
    stocked at opening time.

    Containers are created at start() rather than per task because starting one costs
    far more than a subagent's whole turn. They sit idle on `sleep infinity` and are
    entered with `docker exec` when work arrives, so leasing a slot is free.

    No host directory is mounted. Each run's files live in its own subdirectory of
    base_directory on the host, and a container is handed a copy of one of them for the
    length of a command, at CONTAINER_WORKSPACE_PATH — see SandboxDocker. A mount is
    fixed when a container starts, so reaching every run's files through one would mean
    mounting their parent into every container, and then code written for one user
    could read every other user's runs.

    Leasing is guarded by a lock. Requests are served on several threads at once, and
    two of them taking the same slot would put two runs in one container at the same
    time — each able to read the other's copy.

    Containers are named deterministically, which makes an orphan from a crashed
    process findable: start() removes any container of the same name before creating
    it, so a hard kill costs a stale container rather than a port of corruption.

    The image is built from the Dockerfile in sandbox_image/ unless an image to pull is
    named instead. It is the slim Python base plus pytest — the containers have no
    network, so a test runner has to be in the image for a TEST subagent to run anything.
    The tag is derived from the Dockerfile's contents, so editing it produces a new tag
    and the next start builds the new image instead of reusing a stale one.

    Talking to Docker through its CLI rather than a client library keeps the
    dependency list unchanged and makes every failure legible — the command that
    failed is the command you can paste into a terminal."""

    def __init__(self, size: int = 10, image: Optional[str] = None,
        build_context: Optional[pathlib.Path] = SANDBOX_IMAGE_DIRECTORY,
        base_directory: pathlib.Path | None = None,
        memory_limit: str = "512m", cpu_limit: str = "1.0",
        name_prefix: str = "vela47-slot") -> None:
        if image is None and build_context is None:
            raise ValueError("The pool needs an image to pull or a build context to build one from.")

        self._size: int = size
        self._build_context: Optional[pathlib.Path] = (
            pathlib.Path(build_context) if image is None and build_context is not None else None
        )
        self._image: str = image if image is not None else self._content_tag(pathlib.Path(build_context))
        self._memory_limit: str = memory_limit
        self._cpu_limit: str = cpu_limit
        self._name_prefix: str = name_prefix
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

    @property
    def image(self) -> str:
        return self._image

    def _content_tag(self, build_context: pathlib.Path) -> str:
        digest = hashlib.sha256((build_context / "Dockerfile").read_bytes()).hexdigest()[:12]
        return f"vela47-sandbox:{digest}"

    def _container_name(self, index: int) -> str:
        return f"{self._name_prefix}-{index}"

    def _docker(self, *arguments: str, timeout: int = 120) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["docker", *arguments],
            capture_output = True,
            text = True,
            timeout = timeout,
            check = False
        )

    def start(self) -> None:
        self._base_directory.mkdir(parents = True, exist_ok = True)

        present = self._docker("image", "inspect", self._image, timeout = 30)
        if present.returncode != 0:
            self._provision_image()

        self._slots = []
        for index in range(self._size):
            name = self._container_name(index)
            self._docker("rm", "-f", name, timeout = 30)

            created = self._docker(
                "run", "-d",
                "--name", name,
                "--network", "none",
                "--memory", self._memory_limit,
                "--cpus", self._cpu_limit,
                "--pids-limit", "256",
                self._image,
                "sleep", "infinity"
            )

            if created.returncode != 0:
                self.shutdown()
                raise RuntimeError(
                    f"Could not start sandbox container '{name}': {created.stderr.strip()}"
                )

            self._slots.append(SandboxSlot(
                id = index,
                reference = created.stdout.strip()[:12] or name
            ))

        self._busy = set()

    def _provision_image(self) -> None:
        if self._build_context is None:
            pulled = self._docker("pull", self._image, timeout = 600)
            if pulled.returncode != 0:
                raise RuntimeError(f"Could not pull image '{self._image}': {pulled.stderr.strip()}")
            return

        built = self._docker("build", "-t", self._image, str(self._build_context), timeout = 900)
        if built.returncode != 0:
            raise RuntimeError(
                f"Could not build image '{self._image}' from {self._build_context}: "
                f"{built.stderr.strip()[-2000:]}"
            )

    def shutdown(self) -> None:
        for index in range(self._size):
            try:
                self._docker("rm", "-f", self._container_name(index), timeout = 30)
            except Exception:
                continue
        self._slots = []
        self._busy = set()

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
                f"Increase the pool size or reduce how many subagents run at once."
            )

    def release(self, slot: SandboxSlot) -> None:
        with self._lock:
            self._busy.discard(slot.id)

    def env_for(self, slot: SandboxSlot, run_id: str) -> SandboxEnv:
        return SandboxDocker(
            container_name = self._container_name(slot.id),
            host_directory = self._base_directory / run_id,
            container_directory = CONTAINER_WORKSPACE_PATH
        )

    @property
    def available(self) -> int:
        return len(self._slots) - len(self._busy)

    def __len__(self) -> int:
        return len(self._slots)
