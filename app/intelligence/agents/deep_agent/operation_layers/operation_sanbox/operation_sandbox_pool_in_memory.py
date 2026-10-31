from app.intelligence.agents.deep_agent.operation_layers.operation_sanbox.operation_sandbox_slot import OperationSandboxSlot
from app.intelligence.agents.deep_agent.operation_layers.operation_sanbox.operation_sandbox_pool_base import OperationSandboxPoolBase


class OperationInMemorySandboxPool(OperationSandboxPoolBase):
    """Sandbox pool that tracks slot occupancy without provisioning anything.
    Enforces the same capacity contract as a real backend — a fixed number of
    slots, acquire fails when all are taken — so the subagents layer can be
    built and tested against pool semantics before any container runtime exists.
    Swapping in a Docker-backed pool later changes no caller, because the layer
    depends on OperationSandboxPoolBase rather than on this class."""

    def __init__(self, size: int = 10) -> None:
        self._slots: list[OperationSandboxSlot] = [OperationSandboxSlot(id = index) for index in range(size)]
        self._busy: set[int] = set()

    def acquire(self) -> OperationSandboxSlot:
        for current_slot in self._slots:
            if current_slot.id not in self._busy:
                self._busy.add(current_slot.id)
                return current_slot
        raise RuntimeError(
            f"No sandbox slot available — all {len(self._slots)} are in use. "
            f"Increase the pool size or reduce how many subagents run at once."
        )

    def release(self, slot: OperationSandboxSlot) -> None:
        self._busy.discard(slot.id)

    @property
    def available(self) -> int:
        return len(self._slots) - len(self._busy)

    def __len__(self) -> int:
        return len(self._slots)
