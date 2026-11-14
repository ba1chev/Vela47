import boto3
import pathlib
import tempfile
import threading
from typing import Any, Optional
from botocore.config import Config

from app.intelligence.sandbox import SandboxEnv
from app.intelligence.sandbox import SandboxSlot
from app.intelligence.sandbox import SandboxLambda
from app.intelligence.sandbox import SandboxPoolBase


class SandboxPoolLambda(SandboxPoolBase):
    """A fixed number of slots over one Lambda function, the production sandbox (see
    SandboxLambda). There is nothing to start or stop: Lambda brings up an environment
    per concurrent request and nothing is paid while none runs. The slots keep the pool's
    contract all the same, so at most size commands run at once, however many users
    there are, and acquire() raises when all are taken.

    Every slot names the same function, and the run's directory lives on the server
    under base_directory, as with every other pool. Leasing is guarded by a lock."""

    def __init__(self, function_name: str, region_name: str, size: int = 10,
        base_directory: Optional[pathlib.Path] = None, client: Optional[Any] = None) -> None:
        self._function_name: str = function_name
        self._client: Any = client if client is not None else boto3.client(
            "lambda",
            region_name = region_name,
            config = Config(read_timeout = 150, retries = {"mode": "standard", "max_attempts": 3})
        )
        self._slots: list[SandboxSlot] = [SandboxSlot(id = index, reference = function_name) for index in range(size)]
        self._busy: set[int] = set()
        self._lock: threading.Lock = threading.Lock()
        self._base_directory: pathlib.Path = (
            pathlib.Path(base_directory)
            if base_directory is not None
            else pathlib.Path(tempfile.mkdtemp(prefix = "vela47-"))
        )

    @property
    def base_directory(self) -> pathlib.Path:
        return self._base_directory

    def acquire(self) -> SandboxSlot:
        with self._lock:
            for current_slot in self._slots:
                if current_slot.id not in self._busy:
                    self._busy.add(current_slot.id)
                    return current_slot
        raise RuntimeError(
            f"No sandbox slot available — all {len(self._slots)} are in use. "
            f"Try again once a running step has finished."
        )

    def release(self, slot: SandboxSlot) -> None:
        with self._lock:
            self._busy.discard(slot.id)

    def env_for(self, slot: SandboxSlot, run_id: str) -> SandboxEnv:
        return SandboxLambda(
            function_name = self._function_name,
            host_directory = self._base_directory / run_id,
            client = self._client,
            identifier = f"lambda-slot-{slot.id}"
        )

    @property
    def available(self) -> int:
        return len(self._slots) - len(self._busy)

    def __len__(self) -> int:
        return len(self._slots)
