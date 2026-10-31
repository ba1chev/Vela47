import pathlib
import tempfile

from app.intelligence.sandbox import SandboxSlot
from app.intelligence.sandbox import SandboxPoolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.sandbox import SandboxEnvLocal


class SandboxPoolInMemory(SandboxPoolBase):
    """Sandbox pool that tracks slot occupancy without provisioning anything.
    Enforces the same capacity contract as a real backend — a fixed number of
    slots, acquire fails when all are taken — so the subagents layer can be
    built and tested against pool semantics before any container runtime exists.
    Swapping in a Docker-backed pool later changes no caller, because the layer
    depends on SandboxPoolBase rather than on this class."""

    def __init__(self, size: int = 10, base_directory: pathlib.Path | None = None) -> None:
        self._slots: list[SandboxSlot] = [SandboxSlot(id = index) for index in range(size)]
        self._busy: set[int] = set()
        self._base_directory: pathlib.Path = (
            pathlib.Path(base_directory)
            if base_directory is not None
            else pathlib.Path(tempfile.mkdtemp(prefix = "vela47-"))
        )

    def acquire(self) -> SandboxSlot:
        for current_slot in self._slots:
            if current_slot.id not in self._busy:
                self._busy.add(current_slot.id)
                return current_slot
        raise RuntimeError(
            f"No sandbox slot available — all {len(self._slots)} are in use. "
            f"Increase the pool size or reduce how many subagents run at once."
        )

    def release(self, slot: SandboxSlot) -> None:
        self._busy.discard(slot.id)

    def env_for(self, slot: SandboxSlot, run_id: str) -> SandboxEnv:
        return SandboxEnvLocal(
            root = self._base_directory / run_id,
            identifier = f"local-slot-{slot.id}"
        )

    @property
    def base_directory(self) -> pathlib.Path:
        return self._base_directory

    @property
    def available(self) -> int:
        return len(self._slots) - len(self._busy)

    def __len__(self) -> int:
        return len(self._slots)
