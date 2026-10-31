from abc import ABC, abstractmethod

from app.intelligence.sandbox import SandboxEnv
from app.intelligence.sandbox import SandboxSlot


class SandboxPoolBase(ABC):
    """Abstract base for a fixed-size pool of pre-provisioned execution
    environments, operated like a vending machine: the pool is filled once up
    front, callers take a slot while they need one and put it back when done,
    and the pool never grows on demand. The fixed size is the point — it caps
    how many subagents can run concurrently, so the subagents layer does not
    need its own concurrency limit.

    acquire() raises when nothing is free rather than blocking or allocating,
    which surfaces over-subscription as an error the caller can report instead
    of a hang. Implementations must tolerate release() of an already-free slot
    so a caller's finally-block is always safe to run."""

    @abstractmethod
    def acquire(self) -> SandboxSlot:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def release(self, slot: SandboxSlot) -> None:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def env_for(self, slot: SandboxSlot, run_id: str) -> SandboxEnv:
        raise NotImplementedError("Must be implemented")

    @property
    @abstractmethod
    def available(self) -> int:
        raise NotImplementedError("Must be implemented")

    def start(self) -> None:
        return None

    def shutdown(self) -> None:
        return None
