import pathlib
import tempfile
import subprocess

from app.intelligence.sandbox import SandboxEnv
from app.intelligence.sandbox import SandboxSlot
from app.intelligence.sandbox import SandboxDocker
from app.intelligence.sandbox import SandboxPoolBase

CONTAINER_MOUNT_PATH = "/runs"


class SandboxPoolDocker(SandboxPoolBase):
    """A fixed set of containers started once and reused, like a vending machine
    stocked at opening time.

    Containers are created at start() rather than per task because starting one costs
    far more than a subagent's whole turn. They sit idle on `sleep infinity` and are
    entered with `docker exec` when work arrives, so leasing a slot is free.

    One host directory is mounted into every container. Each run works in its own
    subdirectory of it, which is what lets a slot be leased per task while the files
    stay with the run — a container's mount cannot be changed after it starts, so
    mounting the parent and addressing a child is the only way to get both.

    Containers are named deterministically, which makes an orphan from a crashed
    process findable: start() removes any container of the same name before creating
    it, so a hard kill costs a stale container rather than a port of corruption.

    Talking to Docker through its CLI rather than a client library keeps the
    dependency list unchanged and makes every failure legible — the command that
    failed is the command you can paste into a terminal."""

    def __init__(self, size: int = 10, image: str = "python:3.12-slim",
        base_directory: pathlib.Path | None = None,
        memory_limit: str = "512m", cpu_limit: str = "1.0",
        name_prefix: str = "vela47-slot") -> None:
        self._size: int = size
        self._image: str = image
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

    @property
    def base_directory(self) -> pathlib.Path:
        return self._base_directory

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

        pulled = self._docker("image", "inspect", self._image, timeout = 30)
        if pulled.returncode != 0:
            pull = self._docker("pull", self._image, timeout = 600)
            if pull.returncode != 0:
                raise RuntimeError(
                    f"Could not pull image '{self._image}': {pull.stderr.strip()}"
                )

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
                "-v", f"{self._base_directory}:{CONTAINER_MOUNT_PATH}",
                "-w", CONTAINER_MOUNT_PATH,
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

    def shutdown(self) -> None:
        for index in range(self._size):
            try:
                self._docker("rm", "-f", self._container_name(index), timeout = 30)
            except Exception:
                continue
        self._slots = []
        self._busy = set()

    def acquire(self) -> SandboxSlot:
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
        self._busy.discard(slot.id)

    def env_for(self, slot: SandboxSlot, run_id: str) -> SandboxEnv:
        return SandboxDocker(
            container_name = self._container_name(slot.id),
            host_directory = self._base_directory / run_id,
            container_directory = f"{CONTAINER_MOUNT_PATH}/{run_id}"
        )

    @property
    def available(self) -> int:
        return len(self._slots) - len(self._busy)

    def __len__(self) -> int:
        return len(self._slots)
