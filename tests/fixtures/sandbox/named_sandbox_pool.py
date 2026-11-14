from app.intelligence.sandbox import SandboxSlot
from app.intelligence.sandbox import SandboxPoolInMemory


class NamedSandboxPool(SandboxPoolInMemory):
    """An in-memory pool whose slots carry a container name like a Docker pool's, so the
    code that hands slot references on can be tested without containers."""

    def __init__(self, size: int = 3, base_directory = None) -> None:
        super().__init__(size = size, base_directory = base_directory)
        self._slots = [SandboxSlot(id = index, reference = f"vela47-slot-{index}") for index in range(size)]
